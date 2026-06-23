from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


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
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """The concrete implementation of the tool's action."""
        pass
