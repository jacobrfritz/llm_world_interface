# src/llm_world_interface/main.py
import logging
from pathlib import Path

from .config.settings import settings
from .connectors.gcal_connector import GoogleCalendarConnector
from .connectors.obsidian_connector import ObsidianConnector
from .core.agent import LifeManagerAgent
from .core.llm_factory import LLMFactory
from .logger import get_logger, setup_logging

logger = get_logger(__name__)


def run() -> None:
    """Core application logic demonstrating robust logging and orchestrator."""
    # Configure logging: console logs at INFO level, file logs at DEBUG level
    log_file = Path("logs/app.log")
    setup_logging(
        log_file=log_file,
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        rotation_type="size",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5,
    )

    logger.info("Initializing Life Manager Orchestrator application...")

    # 1. Initialize concrete connectors (Dependency Injection)
    vault_path = settings.obsidian_vault_path
    logger.info("Initializing Obsidian Connector...", extra={"vault_path": vault_path})
    obsidian = ObsidianConnector(vault_root=vault_path)

    logger.info("Initializing Google Calendar Connector...")
    gcal = GoogleCalendarConnector(
        credentials_path=settings.gcal_credentials_path,
        token_path=settings.gcal_token_path,
        calendar_id=settings.gcal_calendar_id,
    )

    # 2. Initialize the preferred LLM (Gemini by default)
    provider = settings.llm_provider
    model_name = settings.llm_model_name
    temperature = settings.llm_temperature

    logger.info(
        "Initializing LLM provider...",
        extra={
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
        },
    )

    try:
        llm = LLMFactory.get_llm(
            provider=provider, model_name=model_name, temperature=temperature
        )
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise e

    # 3. Inject dependencies into the LangGraph orchestrator
    logger.info("Setting up LangGraph Agent Orchestrator...")
    agent = LifeManagerAgent(llm=llm, connectors=[obsidian, gcal])

    # 4. Execute test run
    user_request = (
        "Draft a research note on decentralized energy and schedule 1 hour on "
        "Friday to review it."
    )
    logger.info("Executing test request...", extra={"request": user_request})

    try:
        response = agent.run(user_request)
        logger.info("Test execution completed successfully.")
        print(f"\nFinal Agent Response: {response}")
    except Exception as e:
        logger.exception("An error occurred during agent execution")
        raise e
