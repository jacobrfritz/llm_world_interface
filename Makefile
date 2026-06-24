.PHONY: install test test-watch test-cov lint format typecheck run gui

install:
	uv sync

test:
	uv run pytest

test-watch:
	uv run ptw

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

run:
	uv run llm_world_interface

gui:
	uv run chainlit run src/llm_world_interface/app.py
