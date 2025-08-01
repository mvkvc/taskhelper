help:
    @just --list

deps:
    uv sync

clean: 
    rm -rf .direnv/ .ruff_cache/ .tasks/ .venv/ build/ taskhelper.egg-info/ .tasks.db

dev *args:
    uv run python -m taskhelper.cli {{args}}

run-mcp *args:
    uvx --from . taskhelper-mcp {{args}}

run-cli *args:
    uvx --from . taskhelper {{args}}

format:
    uv run ruff format

lint:
    -uv run ruff format --check
    -uv run ruff check
    -uv run ty check

fix: format
    uv run ruff check --fix

test:
    uv run pytest

check: format lint test
