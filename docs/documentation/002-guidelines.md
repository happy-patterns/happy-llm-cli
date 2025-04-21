---
id: DOC-002
title: Labeling and Referencing Guidelines
description: Defines the labeling scheme for documentation and code references.
tags: [guidelines, labeling]
---

# Labeling and Referencing Guidelines

To maintain consistency and traceability:

- Documentation files use the prefix `DOC-###` in their `id` metadata.
- Task definitions use the prefix `TASK-<phase>.<subtask>` in their `id`.
  - Example: `TASK-6.1.3` for Phase 6, task 1, subtask 3.
- Orchestration subtasks use `orchestrate_<step>_<task>` naming.
- Code modules can use `CODE-###` if needed for future Sphinx labels.
- Front-matter `id` in markdown should match the file naming pattern:
  - `DOC-001` → `001-overview.md`.
- Tags in front-matter help categorize documents for navigation and search.

## Author Guidelines

- Keep documentation focused and concise.
- Use relative links between docs.
  - Update the index (`DOC-000`) when adding new docs.
  - Ensure one source of truth: major references point to actual config files
    (e.g., `orchestration/runbook.yaml` for task statuses).
  - For orchestration task YAML files under `orchestration/tasks/`, include at the very top:
    ```yaml
    # yaml-language-server: $schema none
    ```
    to disable default Ansible schema validation in VS Code YAML extension.
