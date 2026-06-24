from datetime import datetime
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

from llm_world_interface.connectors.base import BaseConnector


class LifeManagerAgent:
    def __init__(self, llm: BaseChatModel, connectors: list[BaseConnector]):
        self.llm = llm
        self.tools = self._bind_connectors(connectors)
        current_time = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")

        # Build available tools information
        tool_names = [tool.name for tool in self.tools]
        tool_list = (
            ", ".join(f"`{name}`" for name in tool_names) if tool_names else "None"
        )

        self.system_prompt = (
            "You are a life management orchestrator. Route tasks to the "
            "correct tools based on user input.\n"
            f"Current system time: {current_time}.\n"
            f"Available tools: {tool_list}.\n\n"
            "System Capabilities & Tool Integration Guidelines:\n"
            "1. Obsidian (`create_obsidian_note`): A workspace for capturing "
            "information, organizing thoughts/tasks, and linking them together "
            "logically using wikilinks (`related_links`). It can also function "
            "as a schedule/reminder system by setting the `due_date` field in "
            "the frontmatter. For example, reminders, grocery lists, or tasks "
            "can be recorded in notes and logically linked to related concepts "
            "(e.g. linking a grocery list to 'buying stuff').\n"
            "2. Google Calendar (`schedule_calendar_event`): Specifically for "
            "blocking time/scheduling events on the user's Google Calendar.\n\n"
            "Execution Instructions:\n"
            "- ONLY claim to have successfully performed an action if you "
            "actually executed the corresponding tool.\n"
            "- If a user requests scheduling or setting a reminder and the "
            "`schedule_calendar_event` tool is NOT available, do NOT claim "
            "you scheduled it on Google Calendar. Instead, record the "
            "reminder/schedule in Obsidian by calling `create_obsidian_note` "
            "with the appropriate `due_date` and task content, and let the "
            "user know you have saved it as a dated task/reminder in Obsidian."
        )

        # Build the LangGraph state machine
        self.graph = self._build_graph()

    def _bind_connectors(self, connectors: list[BaseConnector]) -> list[StructuredTool]:
        # Maps our SOLID connectors to LangChain/LangGraph's expected tool format
        langchain_tools = []
        for connector in connectors:
            tool = StructuredTool.from_function(
                func=connector.execute,
                name=connector.name,
                description=connector.description,
                args_schema=connector.args_schema,
            )
            langchain_tools.append(tool)
        return langchain_tools

    def _build_graph(self) -> Any:
        # LangGraph prebuilt agent handles the ReAct logic and tool cycles
        return create_react_agent(
            model=self.llm, tools=self.tools, prompt=self.system_prompt
        )

    def run(self, user_input: str, config: Any | None = None) -> str:
        # LangGraph operates on a state dictionary containing a list of messages
        inputs = {"messages": [HumanMessage(content=user_input)]}

        # Invoke the graph to completion and get the final state
        result = self.graph.invoke(inputs, config=config)

        # Extract the content of the last AI message
        final_message = result["messages"][-1].content
        if isinstance(final_message, list):
            extracted_texts = []
            for item in final_message:
                if isinstance(item, dict) and item.get("type") == "text":
                    extracted_texts.append(item.get("text", ""))
                elif isinstance(item, str):
                    extracted_texts.append(item)
                else:
                    extracted_texts.append(str(item))
            return "\n".join(extracted_texts)
        return str(final_message)
