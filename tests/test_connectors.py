import os
import tempfile
from datetime import date, datetime
from typing import Any

import pytest
from llm_world_interface.connectors.gcal_connector import GoogleCalendarConnector
from llm_world_interface.connectors.obsidian_connector import ObsidianConnector
from pydantic import ValidationError


def test_obsidian_connector_success() -> None:
    with tempfile.TemporaryDirectory() as tmp_vault:
        connector = ObsidianConnector(vault_root=tmp_vault)

        note_data = {
            "title": "Decentralized Energy",
            "folder": "/research/energy",
            "content": "This is a note about decentralized energy systems.",
            "tags": ["energy", "decentralization"],
            "due_date": date(2026, 6, 25),
            "related_links": ["Smart Grids", "Solar Power"],
        }

        result = connector.execute(**note_data)

        assert result["status"] == "success"
        file_path = result["path"]
        assert os.path.exists(file_path)

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Verify frontmatter formatting
        assert "due_date: 2026-06-25" in content
        assert "tags: ['energy', 'decentralization']" in content

        # Verify content exists and only once (no duplication bug)
        assert "This is a note about decentralized energy systems." in content
        assert content.count("This is a note about decentralized energy systems.") == 1

        # Verify wikilinks are formatted at the bottom
        assert "## Related" in content
        assert "- [[Smart Grids]]" in content
        assert "- [[Solar Power]]" in content


def test_obsidian_connector_validation_error() -> None:
    connector = ObsidianConnector(vault_root="./vault")

    # Missing required field title
    with pytest.raises(ValidationError):
        connector.execute(content="Missing title")


def test_gcal_connector_success() -> None:
    # Create a mock Google Calendar service
    class MockEvent:
        def get(self, key: str) -> str:
            if key == "id":
                return "mock_id_123"
            elif key == "htmlLink":
                return "https://calendar.google.com/event"
            return ""

    class MockEventsResource:
        def insert(self, calendarId: str, body: dict[str, Any]) -> "MockEventsResource":  # noqa: N803
            self.calendar_id = calendarId
            self.body = body
            return self

        def execute(self) -> MockEvent:
            return MockEvent()

    class MockCalendarsResource:
        def get(self, calendarId: str) -> "MockCalendarsResource":  # noqa: N803
            self.calendar_id = calendarId
            return self

        def execute(self) -> dict[str, Any]:
            return {"timeZone": "America/New_York"}

    class MockCalendarService:
        def __init__(self) -> None:
            self._events = MockEventsResource()
            self._calendars = MockCalendarsResource()

        def events(self) -> MockEventsResource:
            return self._events

        def calendars(self) -> MockCalendarsResource:
            return self._calendars

    mock_service = MockCalendarService()
    connector = GoogleCalendarConnector(service=mock_service)

    event_data = {
        "summary": "Decentralized Energy Review",
        "start_time": datetime(2026, 6, 26, 14, 0, 0),
        "end_time": datetime(2026, 6, 26, 15, 0, 0),
        "description": "Weekly status review",
        "location": "Online",
    }

    result = connector.execute(**event_data)

    assert result["status"] == "success"
    assert result["event_id"] == "mock_id_123"
    assert result["html_link"] == "https://calendar.google.com/event"
    assert mock_service.events().calendar_id == "primary"
    assert mock_service.events().body["summary"] == "Decentralized Energy Review"
    assert mock_service.events().body["description"] == "Weekly status review"
    assert mock_service.events().body["location"] == "Online"
    assert mock_service.events().body["start"]["timeZone"] == "America/New_York"
    assert mock_service.events().body["end"]["timeZone"] == "America/New_York"


def test_gcal_connector_timezone_aware() -> None:
    from datetime import timedelta, timezone

    class MockEvent:
        def get(self, key: str) -> str:
            if key == "id":
                return "mock_id_123"
            return ""

    class MockEventsResource:
        def insert(self, calendarId: str, body: dict[str, Any]) -> "MockEventsResource":  # noqa: N803
            self.body = body
            return self

        def execute(self) -> MockEvent:
            return MockEvent()

    class MockCalendarService:
        def __init__(self) -> None:
            self._events = MockEventsResource()

        def events(self) -> MockEventsResource:
            return self._events

    mock_service = MockCalendarService()
    connector = GoogleCalendarConnector(service=mock_service)

    tz = timezone(timedelta(hours=2))
    event_data = {
        "summary": "TZ Aware Event",
        "start_time": datetime(2026, 6, 26, 14, 0, 0, tzinfo=tz),
        "end_time": datetime(2026, 6, 26, 15, 0, 0, tzinfo=tz),
    }

    result = connector.execute(**event_data)

    assert result["status"] == "success"
    assert "+02:00" in mock_service.events().body["start"]["dateTime"]
    assert "timeZone" not in mock_service.events().body["start"]


def test_gcal_connector_api_failure() -> None:
    class MockEventsResource:
        def insert(self, calendarId: str, body: dict[str, Any]) -> "MockEventsResource":  # noqa: N803
            return self

        def execute(self) -> Any:
            raise Exception("Google API Error")

    class MockCalendarService:
        def events(self) -> MockEventsResource:
            return MockEventsResource()

    connector = GoogleCalendarConnector(service=MockCalendarService())
    event_data = {
        "summary": "Decentralized Energy Review",
        "start_time": datetime(2026, 6, 26, 14, 0, 0),
        "end_time": datetime(2026, 6, 26, 15, 0, 0),
    }

    result = connector.execute(**event_data)

    assert result["status"] == "error"
    assert "Google Calendar API call failed" in result["message"]
    assert "Google API Error" in result["message"]


def test_gcal_connector_validation_error() -> None:
    connector = GoogleCalendarConnector()

    # Invalid type for start_time
    with pytest.raises(ValidationError):
        connector.execute(
            summary="Event", start_time="invalid-date", end_time=datetime.now()
        )
