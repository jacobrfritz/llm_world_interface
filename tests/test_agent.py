from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from llm_world_interface.connectors.base import BaseConnector
from llm_world_interface.core.agent import LifeManagerAgent
from llm_world_interface.models.note import ObsidianNoteSchema


class DummyToolConnector(BaseConnector):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing."

    @property
    def args_schema(self) -> type[ObsidianNoteSchema]:
        return ObsidianNoteSchema

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"status": "success", "data": kwargs}


class MockLLM(BaseChatModel):
    calls_count: int = 0

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.calls_count += 1

        if self.calls_count == 1:
            # First call: return a tool call
            tool_call = {
                "name": "mock_tool",
                "args": {
                    "title": "Decentralized Energy",
                    "content": "Test content",
                    "folder": "/",
                },
                "id": "call_123",
            }
            message = AIMessage(content="", tool_calls=[tool_call])
        else:
            # Second call: return the final answer
            message = AIMessage(content="Successfully processed and stored the note.")

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock-llm"


def test_agent_orchestration() -> None:
    llm = MockLLM()
    connector = DummyToolConnector()

    agent = LifeManagerAgent(llm=llm, connectors=[connector])

    # Run agent loop
    response = agent.run("Draft a note on decentralized energy")

    # Assert LLM was called at least twice (first for tool, second for completion)
    assert llm.calls_count >= 2
    assert response == "Successfully processed and stored the note."
