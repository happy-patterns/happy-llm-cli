---
id: DOC-003
title: Orchestration System Overview
description: Overview of the orchestration tooling for task management.
tags: [orchestration]
---

# Orchestration System

The orchestration tooling is located under `orchestration/`:

- **`runbook.yaml`**: Master task flow with task entries:
  - Each entry has: `id`, `name`, `status`, `depends_on`, `task_detail_file`, `type`.
- **`tasks/`**: Task detail YAML files for each subtask.
- **`logs/run_log.jsonl`**: Append-only JSONL logs of execution events.
- **`prompt_templates/`**: Directory for AI prompt templates.
- **`run.py`**: Orchestrator script to execute tasks.

## Task Status Lifecycle

Statuses:

- `PENDING`: Task is defined but not yet ready.
- `READY`: Dependencies are met; task can be executed.
- `RUNNING`: Currently executing.
- `DONE`: Completed successfully.
- `ERROR`: Execution failed; manual intervention required.
- `SKIPPED`: Intentionally skipped.

## Workflow

1. `run.py` loads `runbook.yaml` → finds the next `READY` task.
2. Marks as `RUNNING`; executes handler (`MANUAL`, `AI_ASSISTED`, etc.).
3. User inputs drive `DONE`, `ERROR`, or `SKIPPED`.
4. Updates YAML and logs events.
5. Loop until no `READY` tasks remain.
