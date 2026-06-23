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
        self.system_prompt = (
            "You are a life management orchestrator. Route tasks to the "
            "correct tools based on user input."
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

    def run(self, user_input: str) -> str:
        # LangGraph operates on a state dictionary containing a list of messages
        inputs = {"messages": [HumanMessage(content=user_input)]}

        # Invoke the graph to completion and get the final state
        result = self.graph.invoke(inputs)

        # Extract the content of the last AI message
        final_message = result["messages"][-1].content
        if isinstance(final_message, list):
            return "\n".join([str(item) for item in final_message])
        return str(final_message)
