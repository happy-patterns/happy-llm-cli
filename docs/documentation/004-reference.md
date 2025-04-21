---
id: DOC-004
title: Central Reference Systems
description: Defines core reference systems: status states and implementation mappings.
tags: [reference, status, implementation]
---

# Central Reference Systems

## Status Reference

All tasks use a central status model defined in `orchestration/runbook.yaml`:

| Status   | Description                       |
|----------|-----------------------------------|
| PENDING  | Defined but not ready to run      |
| READY    | Dependencies met; ready to run    |
| RUNNING  | Execution in progress             |
| DONE     | Completed successfully            |
| ERROR    | Execution failed; manual action needed |
| SKIPPED  | Execution intentionally skipped   |

## Implementation Mapping

Mapping of orchestration tasks to code in `orchestration/run.py`:

- **`orchestrate_2_yaml_utils`**: Implements `load_yaml`, `save_yaml`.
- **`orchestrate_3_core_loop`**: Main orchestrator loop logic.
- **`orchestrate_4_manual_handler`**: Manual task prompt and status updates.
- **`orchestrate_5_logging`**: JSONL logging on task start/end.
- **`orchestrate_6_ai_handler`**: AI-assisted task execution flow.
- **`orchestrate_7_error_handling`**: Error capture and issues tracking.
- **`orchestrate_8_refine`**: Fallback prompts, automated scripts, CLI options.

For detailed task definitions, refer to `orchestration/runbook.yaml` and `orchestration/tasks/`.
