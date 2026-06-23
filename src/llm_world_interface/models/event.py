from datetime import datetime

from pydantic import BaseModel, Field


class CalendarEventSchema(BaseModel):
    summary: str = Field(..., description="Title of the calendar event.")
    start_time: datetime = Field(..., description="ISO format start time.")
    end_time: datetime = Field(..., description="ISO format end time.")
