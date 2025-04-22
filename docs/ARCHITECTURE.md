---
id: DOC-006
title: Architecture
description: High-level architecture of the Happy LLM CLI tool.
tags: [architecture]
---

# Architecture
This document describes the high-level architecture of the Happy LLM CLI tool.

## Layers

- CLI Layer (`happy_llm_cli/cli.py`): Entry point for CLI commands (e.g., chat); defines user-facing commands.
- Provider Abstraction Layer (`happy_llm_cli/providers/`): Defines `AbstractProviderAdapter`, data models (`ChatMessage`, `ChatRequest`, `ChatResponse`), and concrete adapters (e.g., `OpenAIProvider`).
- Configuration Layer (`happy_llm_cli/utils/config.py`): Loads environment variables (via python-dotenv) and provides configuration utilities.
- Utility Layer (`happy_llm_cli/utils/`): Shared helpers (e.g., `config.py`, `rate_limit.py`).

## Directory Structure
```
happy_llm_cli/
├── cli.py
├── __init__.py
├── providers/
│   ├── base.py
│   ├── openai_provider.py
│   ├── factory.py
│   └── exceptions.py
└── utils/
    ├── config.py
    ├── rate_limit.py
    └── __init__.py
```

## Data Flow
1. User runs `happy_llm chat "<prompt>"`.
2. CLI layer builds a `ChatRequest` and selects the default provider.
3. Provider adapter performs the API call, handling retries and errors.
4. Response is parsed into a `ChatResponse` and displayed.

## Development Orchestration
Development tasks are managed under `orchestration/` via YAML-driven runbooks.
See [Orchestration System Overview](documentation/003-orchestration.md) for details.
