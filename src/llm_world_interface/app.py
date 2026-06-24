# src/llm_world_interface/app.py
import chainlit as cl
from langchain_core.runnables import RunnableConfig

from llm_world_interface.config.settings import settings
from llm_world_interface.connectors.gcal_connector import GoogleCalendarConnector
from llm_world_interface.connectors.obsidian_connector import ObsidianConnector
from llm_world_interface.core.agent import LifeManagerAgent
from llm_world_interface.core.llm_factory import LLMFactory
from llm_world_interface.logger import get_logger

logger = get_logger(__name__)


@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialize the connectors and the agent orchestrator at the start of the chat."""
    # 1. Initialize concrete connectors (Dependency Injection)
    vault_path = settings.obsidian_vault_path
    obsidian = ObsidianConnector(vault_root=vault_path)
    gcal = GoogleCalendarConnector()

    # 2. Initialize the preferred LLM
    provider = settings.llm_provider
    model_name = settings.llm_model_name
    temperature = settings.llm_temperature

    try:
        # LLM initialization might require API keys
        llm = LLMFactory.get_llm(
            provider=provider, model_name=model_name, temperature=temperature
        )
        # 3. Inject dependencies into the LangGraph orchestrator
        agent = LifeManagerAgent(llm=llm, connectors=[obsidian, gcal])
        cl.user_session.set("agent", agent)  # type: ignore[no-untyped-call]

        await cl.Message(
            content=(
                f"🤖 **Life Manager Agent Initialized**\n\n"
                f"* **LLM Provider**: `{provider}`\n"
                f"* **Model Name**: `{model_name}`\n"
                f"* **Obsidian Vault**: `{vault_path}`\n\n"
                f"How can I help you today?"
            )
        ).send()  # type: ignore[no-untyped-call]
    except Exception as e:
        logger.exception("Failed to initialize LangGraph agent")
        await cl.Message(
            content=(
                f"❌ **Failed to initialize Agent**\n\n"
                f"Error: `{str(e)}`\n\n"
                f"Please ensure you have configured your `.env` file "
                f"correctly with appropriate API keys."
            )
        ).send()  # type: ignore[no-untyped-call]


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming user messages and run the agent orchestrator."""
    agent: LifeManagerAgent | None = cl.user_session.get("agent")  # type: ignore[no-untyped-call]
    if not agent:
        await cl.Message(
            content="Agent not initialized. Please restart the session."
        ).send()  # type: ignore[no-untyped-call]
        return

    # Attempt to load Chainlit's LangChain callback handler for step visualization
    callbacks = []
    try:
        from chainlit.langchain.callbacks import LangchainCallbackHandler

        cb = LangchainCallbackHandler()
        callbacks.append(cb)
    except Exception as e:
        logger.warning(f"Could not load Chainlit LangChain callback handler: {e}")

    # Build RunnableConfig to pass callbacks to the LangGraph execution
    config = RunnableConfig(
        callbacks=callbacks,  # type: ignore[typeddict-item]
        configurable={"thread_id": cl.context.session.id},
    )

    try:
        # Run agent.run asynchronously in a background thread to prevent blocking
        # since agent.run currently calls graph.invoke synchronously
        response = await cl.make_async(agent.run)(message.content, config=config)

        # Send final agent response
        await cl.Message(content=response).send()  # type: ignore[no-untyped-call]
    except Exception as e:
        logger.exception("An error occurred during agent execution")
        await cl.Message(content=f"⚠️ **Error running agent:**\n`{str(e)}`").send()  # type: ignore[no-untyped-call]
