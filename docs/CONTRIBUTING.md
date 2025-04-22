# Contributing Guidelines
Thank you for your interest in contributing to Happy LLM CLI. This document outlines the development workflow, coding standards, and tools used in the project.

## Development Environment

We provide a containerized development environment for consistency:

### Option 1: Command Line Container

1. Build the development image:
   ```bash
   podman build -t happy-llm-cli-dev -f Containerfile .
   ```
   
   Alternatively, if using Docker:
   ```bash
   docker build -t happy-llm-cli-dev -f Containerfile .
   ```

2. Run the container with project volume and env file:
   ```bash
   podman run -it --rm \
     -v $(pwd):/home/devuser/app:Z \
     --env-file .env \
     --name happy_llm-dev-instance \
     happy-llm-cli-dev \
     /bin/bash
   ```
   
   Alternatively, if using Docker:
   ```bash
   docker run -it --rm \
     -v $(pwd):/home/devuser/app \
     --env-file .env \
     --name happy_llm-dev-instance \
     happy-llm-cli-dev \
     /bin/bash
   ```

3. Inside the container, activate the virtual environment and install dependencies:
   ```bash
   source .venv/bin/activate
   pip install -e .    # Install project dependencies and console scripts
   ```

### Option 2: VS Code Remote Containers

For a more integrated development experience, we provide VS Code Remote Containers configuration:

1. Install the [Remote Development extension pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack) in VS Code.

2. Open the project folder in VS Code.

3. Click on the green Remote button in the bottom-left corner of VS Code, or press F1 and select "Remote-Containers: Reopen in Container".

4. VS Code will build the container (if needed) and open the project in the container with all the recommended extensions and settings pre-configured.

### Option 3: Local Environment

Alternatively, set up a local Python 3.10+ virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .    # Install project dependencies and console scripts
```

## Orchestration System

We use a YAML-driven orchestrator for development tasks:
- `orchestration/runbook.yaml`: Master task list
- `orchestration/tasks/`: Per-task detail files
- `orchestration/run.py`: Script to execute tasks
- `orchestration/logs/run_log.jsonl`: Execution logs
To bootstrap or continue tasks (run from project root):
```bash
# run directly from the project root
python3 orchestration/run.py

# or via module invocation (Python will locate the `orchestration` package):
python3 -m orchestration.run

# or via console script (after `pip install -e .`):
happy-llm-orchestrate
```
Follow the interactive prompts for manual and AI-assisted steps.

## Coding Standards
- **Naming**: See `docs/planning/plan.md` conventions
- **Style**: PEP 8 via pre-commit (Ruff for linting & formatting)
- **Type Checking**: MyPy for static type verification
- **Type Hints**: Use annotations for public interfaces

## Testing
- Tests in `tests/`
- Run with:
  ```bash
  pytest
  ```

## Documentation
See `docs/documentation/index.md` for detailed docs on:
- Project overview
- Development guidelines
- Orchestration system
- Reference materials

## Workflow
- Use feature branches and descriptive commits (e.g., Conventional Commits)
- Ensure tests pass and docs updated before PR submission
