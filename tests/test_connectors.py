import os
import tempfile
from datetime import date, datetime

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
    connector = GoogleCalendarConnector()

    event_data = {
        "summary": "Decentralized Energy Review",
        "start_time": datetime(2026, 6, 26, 14, 0, 0),
        "end_time": datetime(2026, 6, 26, 15, 0, 0),
    }

    result = connector.execute(**event_data)

    assert result["status"] == "success"
    assert result["event_id"] == "mock_id_123"


def test_gcal_connector_validation_error() -> None:
    connector = GoogleCalendarConnector()

    # Invalid type for start_time
    with pytest.raises(ValidationError):
        connector.execute(
            summary="Event", start_time="invalid-date", end_time=datetime.now()
        )
