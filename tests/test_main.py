# tests/test_main.py
from unittest.mock import MagicMock, patch

import pytest
from llm_world_interface import main


@patch("llm_world_interface.main.LLMFactory")
@patch("llm_world_interface.main.LifeManagerAgent")
def test_run(
    mock_agent_class: MagicMock,
    mock_llm_factory: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Set up mock agent instance
    mock_agent = MagicMock()
    mock_agent.run.return_value = "Mocked Agent Response"
    mock_agent_class.return_value = mock_agent

    # Set up mock llm
    mock_llm = MagicMock()
    mock_llm_factory.get_llm.return_value = mock_llm

    # Run main logic
    main.run()

    # Assert agent run was called with the user request
    mock_agent.run.assert_called_once_with(
        "Draft a research note on decentralized energy and schedule "
        "1 hour on Friday to review it."
    )

    # Verify print output
    captured = capsys.readouterr()
    assert "Final Agent Response: Mocked Agent Response" in captured.out
