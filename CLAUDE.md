# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands
- Install in dev mode: `pip install -e .`
- Run tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function`
- Lint code: `ruff check .`
- Format code: `ruff format .`
- Type check: `mypy happy_llm_cli`
- Run orchestrator: `python -m orchestration.run` or `happy-llm-orchestrate`

## Code Style Guidelines
- **Naming**: PascalCase for classes, snake_case for functions/variables, ALL_CAPS for constants
- **Imports**: Organized alphabetically
- **Type Hints**: Required for public interfaces (PEP 484)
- **Line Length**: 88 characters max
- **Indentation**: 4 spaces (Python standard)
- **Error Handling**: Use custom exceptions from `providers.exceptions`
- **CLI Design**: Use Typer framework with kebab-case flags
- **Architecture**: Providers must implement `AbstractProviderAdapter`
- **Python Version**: 3.10+
- **Documentation**: Docstrings for all public functions, methods, and classes
- **Pre-commit Hooks**: Project uses black, ruff, mypy, and pre-commit hooks