# HAPPY-LLM-CLI

Python CLI tool for interacting with Large Language Models via an abstract provider layer.

## Installation

```bash
pip install happy-llm-cli
```

## Environment Setup

Copy the example file and set your OpenAI API key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

## Usage

Send a prompt to the model:

```bash
happy-llm chat "Hello, world!"
```

## Development

Happy LLM CLI includes a YAML-driven orchestrator for bootstrapping and managing development tasks.
See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for full development setup and workflow.
To install the CLI and orchestration entry points locally (editable mode), run from the project root:
```bash
pip install -e .
```

To run the orchestrator (ensure you are in the project root directory):
```bash
# using direct script
python3 orchestration/run.py

# or as a module (works from any subdirectory within the repo):
python3 -m orchestration.run
```

## Documentation

Full project documentation resides in the `docs/` folder.
Browse the [Documentation Index](docs/documentation/index.md) for detailed guides on development and reference, or see the [Architecture Overview](docs/ARCHITECTURE.md).
