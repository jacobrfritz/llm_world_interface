System Architecture Specification: AI Life Manager1. OverviewThis document outlines the architecture for a local, Python-based AI orchestration system. The system ingests user input (text/audio transcriptions), processes the intent via a Large Language Model (LLM), and executes actions across distinct "Connectors" (Obsidian for knowledge management and Google Calendar for scheduling).2. SOLID Design Principles ApplicationTo ensure the system remains modular and extensible, we adhere strictly to SOLID principles:Single Responsibility Principle (SRP): Data validation (Pydantic), LLM orchestration (LangGraph), external API interactions (Connectors), and Model Instantiation (LLMFactory) are isolated into distinct classes.Open/Closed Principle (OCP): The core AgentRouter is open for extension (by registering new tools or passing different LLMs) but closed for modification. You will not need to edit the LLM routing logic to add a new integration or switch AI providers.Liskov Substitution Principle (LSP): All connectors inherit from a BaseConnector class. The core execution engine can trigger any connector interchangeably. Similarly, the agent interacts with any LLM conforming to LangChain's BaseChatModel.Interface Segregation Principle (ISP): Connectors implement specific interfaces (FileStorageProtocol, SchedulingProtocol) rather than a monolithic "AppTool" interface.Dependency Inversion Principle (DIP): The orchestrator depends on abstract interfaces (BaseConnector and BaseChatModel), not concrete implementations (ObsidianConnector or ChatOpenAI/ChatGoogleGenerativeAI).3. Directory Structurelife_manager/
│
├── core/                       # High-level orchestration
│   ├── __init__.py
│   ├── agent.py                # LangGraph state machine & LLM orchestration
│   ├── llm_factory.py          # Factory pattern for multi-LLM support (Gemini, OpenAI, etc.)
│   └── schemas.py              # Pydantic schemas for LLM tool calling
│
├── connectors/                 # Low-level implementation details (The "Tools")
│   ├── __init__.py
│   ├── base.py                 # Abstract Base Classes (Interfaces)
│   ├── obsidian_connector.py   # Obsidian file system logic
│   └── gcal_connector.py       # Google Calendar API logic
│
├── models/                     # Shared data structures
│   ├── note.py                 # Defines what an "Obsidian Note" is
│   └── event.py                # Defines what a "Calendar Event" is
│
├── config/                     # Environment and secrets management
│   └── settings.py
│
└── main.py                     # Entry point
4. Component Specifications4.1. Interfaces & Abstractions (connectors/base.py)To enforce Dependency Inversion and Liskov Substitution, all tools must implement a standard execution method that the LLM orchestrator can call.from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Dict

class BaseConnector(ABC):
    """Abstract base class for all system connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool exposed to the LLM."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description used by the LLM to decide when to use this tool."""
        pass

    @property
    @abstractmethod
    def args_schema(self) -> type[BaseModel]:
        """Pydantic schema defining the expected inputs."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """The concrete implementation of the tool's action."""
        pass
4.2. Data Models (models/note.py)Using Pydantic ensures Single Responsibility. The LLM generates unstructured text, but Pydantic validates and structures it before it ever reaches the Obsidian connector.from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class ObsidianNoteSchema(BaseModel):
    title: str = Field(..., description="A clean, alphanumeric title for the note.")
    folder: str = Field(default="/", description="Vault subdirectory path.")
    content: str = Field(..., description="Markdown formatted body content.")
    tags: List[str] = Field(default_factory=list, description="List of relevant tags without the '#' symbol.")
    due_date: Optional[date] = Field(None, description="Actionable deadline if applicable.")
    related_links: List[str] = Field(default_factory=list, description="Exact titles of related concepts to be linked.")
4.3. The Obsidian Connector (connectors/obsidian_connector.py)This module is strictly responsible for converting a validated ObsidianNoteSchema into physical bytes on the hard drive.import os
from connectors.base import BaseConnector
from models.note import ObsidianNoteSchema

class ObsidianConnector(BaseConnector):
    name = "create_obsidian_note"
    description = "Use this to create or update a research note, task, or mind map node in the user's Obsidian vault."
    args_schema = ObsidianNoteSchema

    def __init__(self, vault_root: str):
        self.vault_root = vault_root

    def _build_frontmatter(self, kwargs) -> str:
        # Internal method to format YAML block
        yaml = "---\n"
        if kwargs.get('due_date'):
            yaml += f"due_date: {kwargs['due_date']}\n"
        if kwargs.get('tags'):
            yaml += f"tags: {kwargs['tags']}\n"
        yaml += "---\n\n"
        return yaml

    def _inject_wikilinks(self, content: str, links: list) -> str:
        # Appends formatted [[Links]] to the bottom of the document
        if not links: return content
        link_block = "\n\n## Related\n" + "\n".join([f"- [[{link}]]" for link in links])
        return content + link_block

    def execute(self, **kwargs) -> dict:
        validated_data = self.args_schema(**kwargs)
        target_dir = os.path.join(self.vault_root, validated_data.folder)
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, f"{validated_data.title}.md")

        full_content = (
            self._build_frontmatter(kwargs) +
            validated_data.content +
            self._inject_wikilinks(validated_data.content, validated_data.related_links)
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return {"status": "success", "path": file_path}
4.4. Google Calendar Connector (connectors/gcal_connector.py)Follows the exact same interface pattern, isolating OAuth and HTTP requests from the rest of the application.from connectors.base import BaseConnector
from pydantic import BaseModel, Field
from datetime import datetime

class CalendarEventSchema(BaseModel):
    summary: str = Field(..., description="Title of the calendar event.")
    start_time: datetime = Field(..., description="ISO format start time.")
    end_time: datetime = Field(..., description="ISO format end time.")

class GoogleCalendarConnector(BaseConnector):
    name = "schedule_calendar_event"
    description = "Use this to block time on the user's Google Calendar."
    args_schema = CalendarEventSchema

    def execute(self, **kwargs) -> dict:
        validated_data = self.args_schema(**kwargs)
        # TODO: Implement Google API Client insertion logic here
        # Return success confirmation
        return {"status": "success", "event_id": "mock_id_123"}
4.5. Multi-Provider LLM Factory (core/llm_factory.py)This factory abstracts away the specific provider libraries (like langchain-google-genai vs langchain-openai). It returns a generalized BaseChatModel that the agent can interact with agnostically.from langchain_core.language_models.chat_models import BaseChatModel

class LLMFactory:
    """Factory to initialize LLM instances based on the requested provider."""

    @staticmethod
    def get_llm(provider: str, model_name: str, **kwargs) -> BaseChatModel:
        if provider.lower() == "gemini":
            # Requires `pip install langchain-google-genai` and GEMINI_API_KEY
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, **kwargs)

        elif provider.lower() == "openai":
            # Requires `pip install langchain-openai` and OPENAI_API_KEY
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, **kwargs)

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
4.6. The Core Orchestrator (core/agent.py)The orchestrator now explicitly uses LangGraph (langgraph.prebuilt.create_react_agent). This replaces the deprecated legacy AgentExecutor and establishes a state-graph foundation for future features like memory handling.from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

class LifeManagerAgent:
    def __init__(self, llm: BaseChatModel, connectors: list):
        self.llm = llm
        self.tools = self._bind_connectors(connectors)
        self.system_prompt = "You are a life management orchestrator. Route tasks to the correct tools based on user input."

        # Build the LangGraph state machine
        self.graph = self._build_graph()

    def _bind_connectors(self, connectors: list) -> list:
        # Maps our SOLID connectors to LangChain/LangGraph's expected tool format
        langchain_tools = []
        for connector in connectors:
            tool = StructuredTool.from_function(
                func=connector.execute,
                name=connector.name,
                description=connector.description,
                args_schema=connector.args_schema
            )
            langchain_tools.append(tool)
        return langchain_tools

    def _build_graph(self):
        # LangGraph prebuilt agent handles the ReAct logic and tool cycles
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            state_modifier=self.system_prompt
        )

    def run(self, user_input: str) -> str:
        # LangGraph operates on a state dictionary containing a list of messages
        inputs = {"messages": [HumanMessage(content=user_input)]}

        # Invoke the graph to completion and get the final state
        result = self.graph.invoke(inputs)

        # Extract the content of the last AI message
        final_message = result["messages"][-1].content
        return final_message
4.7. Application Entry Point (main.py)This top-level file stitches everything together, specifying Gemini as the preferred model and injecting the initialized tools into the agent.import os
from core.agent import LifeManagerAgent
from core.llm_factory import LLMFactory
from connectors.obsidian_connector import ObsidianConnector
from connectors.gcal_connector import GoogleCalendarConnector

if __name__ == "__main__":
    # 1. Initialize concrete connectors (Dependency Injection)
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./my_vault")
    obsidian = ObsidianConnector(vault_root=vault_path)
    gcal = GoogleCalendarConnector()

    # 2. Initialize the preferred LLM (Gemini in this case)
    # Ensure GEMINI_API_KEY is set in your environment
    gemini_llm = LLMFactory.get_llm(
        provider="gemini",
        model_name="gemini-2.5-flash",
        temperature=0.2
    )

    # 3. Inject dependencies into the LangGraph orchestrator
    agent = LifeManagerAgent(llm=gemini_llm, connectors=[obsidian, gcal])

    # 4. Execute test run
    user_request = "Draft a research note on decentralized energy and schedule 1 hour on Friday to review it."

    print("🤖 Processing request...")
    response = agent.run(user_request)
    print(f"\nFinal Response: {response}")
