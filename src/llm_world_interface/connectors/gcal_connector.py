import os.path
from typing import Any

from pydantic import BaseModel

from llm_world_interface.connectors.base import BaseConnector
from llm_world_interface.logger import get_logger
from llm_world_interface.models.event import CalendarEventSchema

logger = get_logger(__name__)


class GoogleCalendarConnector(BaseConnector):
    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
        calendar_id: str = "primary",
        service: Any = None,
    ) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.calendar_id = calendar_id
        self._service = service

    @property
    def name(self) -> str:
        return "schedule_calendar_event"

    @property
    def description(self) -> str:
        return "Use this to block time on the user's Google Calendar."

    @property
    def args_schema(self) -> type[BaseModel]:
        return CalendarEventSchema

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import (  # type: ignore[import-untyped]
            InstalledAppFlow,
        )
        from googleapiclient.discovery import build  # type: ignore[import-untyped]

        # If modifying these scopes, delete the file token.json.
        scopes = ["https://www.googleapis.com/auth/calendar.events"]
        creds = None

        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, scopes)  # type: ignore[no-untyped-call]
            except Exception as e:
                logger.warning(
                    f"Failed to load credentials from {self.token_path}: {e}"
                )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    msg = (
                        "Google Calendar credentials file not found at "
                        f"'{self.credentials_path}'. Please place your OAuth "
                        "client ID credentials JSON at this path."
                    )
                    raise FileNotFoundError(msg)
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, scopes
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            try:
                with open(self.token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to save token to {self.token_path}: {e}")

        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = CalendarEventSchema(**kwargs)

        try:
            service = self._get_service()
        except Exception as e:
            logger.exception("Failed to initialize Google Calendar service")
            return {
                "status": "error",
                "message": f"Failed to initialize Google Calendar service: {e}",
            }

        start_tz = validated_data.start_time.tzinfo
        end_tz = validated_data.end_time.tzinfo

        event_body: dict[str, Any] = {
            "summary": validated_data.summary,
            "start": {
                "dateTime": validated_data.start_time.isoformat(),
            },
            "end": {
                "dateTime": validated_data.end_time.isoformat(),
            },
        }

        # If either start or end time is naive, we must provide a timezone definition.
        if start_tz is None or end_tz is None:
            try:
                # Fetch calendar metadata to get its timezone
                calendar = (
                    service.calendars().get(calendarId=self.calendar_id).execute()
                )
                calendar_timezone = calendar.get("timeZone", "UTC")
            except Exception as e:
                logger.warning(
                    f"Failed to fetch calendar timezone, defaulting to UTC: {e}"
                )
                calendar_timezone = "UTC"

            if start_tz is None:
                event_body["start"]["timeZone"] = calendar_timezone
            if end_tz is None:
                event_body["end"]["timeZone"] = calendar_timezone

        if validated_data.description:
            event_body["description"] = validated_data.description
        if validated_data.location:
            event_body["location"] = validated_data.location

        try:
            event = (
                service.events()
                .insert(calendarId=self.calendar_id, body=event_body)
                .execute()
            )
            return {
                "status": "success",
                "event_id": event.get("id"),
                "html_link": event.get("htmlLink"),
            }
        except Exception as e:
            logger.exception("Google Calendar API call failed")
            return {
                "status": "error",
                "message": f"Google Calendar API call failed: {e}",
            }
