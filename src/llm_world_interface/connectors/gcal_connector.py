from typing import Any

from pydantic import BaseModel

from llm_world_interface.connectors.base import BaseConnector
from llm_world_interface.models.event import CalendarEventSchema


class GoogleCalendarConnector(BaseConnector):
    @property
    def name(self) -> str:
        return "schedule_calendar_event"

    @property
    def description(self) -> str:
        return "Use this to block time on the user's Google Calendar."

    @property
    def args_schema(self) -> type[BaseModel]:
        return CalendarEventSchema

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        _ = CalendarEventSchema(**kwargs)
        # TODO: Implement Google API Client insertion logic here
        # Return success confirmation
        return {"status": "success", "event_id": "mock_id_123"}
