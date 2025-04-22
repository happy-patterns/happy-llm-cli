# Project Plan: Solo Developer Task Orchestration System

## 1. Introduction & Goal

This document outlines the plan for developing a scripting system to manage and execute the predefined task/subtask structure for the `happy-llm-cli` project. The primary goal is to create a **simple, linear, and manageable workflow** for a solo developer that integrates status tracking, error handling, AI prompt execution (via OpenAI API), logging, and allows for easy manual intervention and review.

The system will orchestrate the execution of tasks defined in the YAML structures generated previously, treating the development process like working through a sequential playbook.

## 2. Core Principles

* **Simplicity First:** Prioritize straightforward implementation over complex frameworks. Start minimal and add features as needed.
* **Linear Flow:** The primary mode of operation involves processing tasks sequentially based on dependencies.
* **YAML Driven:** Use YAML files for defining the task flow and storing detailed task information, allowing easy manual review and editing.
* **Explicit States:** Clearly track the status of each task.
* **Actionable Errors:** Errors should halt relevant parts of the process and provide clear information for manual resolution or triggering fallbacks.
* **Reproducibility & Auditability:** Log key information about each task execution, especially AI prompts and outcomes.

## 3. Proposed System Architecture (Simplified for Solo Dev)

We'll adopt a pragmatic approach centered around a primary control script and structured data files:

1. **Runbook File (`runbook.yaml`):** The master file defining the sequence of major tasks (Phases or groups of subtasks), their dependencies, and overall status. This drives the linear workflow.
2. **Task Detail Files (`tasks/<task_id>.yaml`):** Individual files for each granular task/subtask. Contains the specific prompt, parameters, status, output location, error details, etc. Linked from the `runbook.yaml`.
3. **Orchestrator Script (`run.py`):** The main Python script that reads the `runbook.yaml`, identifies the next actionable task, executes it (either manually guided or by calling the AI API), updates status, and logs results.
4. **Prompt Templates (`prompt_templates/`):** Reusable text files or templates (e.g., using f-strings or Jinja2) for constructing AI prompts, referenced in Task Detail Files.
5. **Log Files (`logs/`):** Append-only logs (e.g., JSONL or plain text) recording actions, prompt executions, errors, and outcomes.
6. **Output Artifacts (`outputs/`):** Directory where generated code, documentation, etc., are stored, referenced in Task Detail Files.

## 4. Key Components & Implementation Details

### 4.1. Runbook File (`runbook.yaml`)

* **Structure:** A list of task entries. Each entry represents a logical step (could be a Phase from the original plan or a significant subtask group).
* **Fields per Entry:**
  * `id`: Unique identifier (e.g., `phase_0_setup`, `task_2.1_implement_abc`)
  * `name`: Human-readable name.
  * `status`: (`PENDING`, `READY`, `RUNNING`, `DONE`, `ERROR`, `SKIPPED`)
  * `depends_on`: List of `id`s this task requires to be `DONE`.
  * `task_detail_file`: Path to the corresponding Task Detail File (e.g., `tasks/task_2.1.yaml`).
  * `type`: (`MANUAL`, `AI_ASSISTED`, `AUTOMATED_SCRIPT`) - Hints for the orchestrator.
* **Purpose:** Provides the high-level linear sequence and dependency overview. The orchestrator uses this to find the next task.

```yaml
# Example runbook.yaml
tasks:
  - id: phase_0_setup
    name: "Phase 0: Project Setup & Environment"
    status: DONE
    depends_on: []
    task_detail_file: tasks/phase_0_summary.yaml # Optional summary/link
    type: MANUAL
  - id: task_2.1_implement_abc
    name: "Phase 1 / Task 2.1: Implement Base Adapter Class"
    status: READY # <-- Orchestrator looks for this
    depends_on: [phase_0_setup]
    task_detail_file: tasks/task_2.1.yaml
    type: AI_ASSISTED
  - id: task_2.2_implement_dataclasses
    name: "Phase 1 / Task 2.2: Implement Core Data Classes"
    status: PENDING
    depends_on: [task_2.1_implement_abc] # Depends on the previous step
    task_detail_file: tasks/task_2.2.yaml
    type: AI_ASSISTED
  # ... other tasks
```

### 4.2. Task Detail Files (`tasks/<task_id>.yaml`)

* **Structure:** A dictionary containing all specifics for a *granular* subtask identified previously.
* **Fields:**
  * `id`: Matches the ID used elsewhere.
  * `name`: Human-readable name.
  * `status`: (`PENDING`, `READY`, `RUNNING`, `DONE`, `ERROR`, `SKIPPED`) - Mirrors/updates runbook status.
  * `description`: Detailed description of the task.
  * `type`: (`MANUAL`, `AI_ASSISTED`, `AUTOMATED_SCRIPT`)
  * `ai_details`: (Present if `type == AI_ASSISTED`)
    * `model`: e.g., "gpt-4o-mini"
    * `prompt_template`: Path to template file (e.g., `prompt_templates/generate_abc.txt`)
    * `input_context`: Key-value pairs or context needed to fill the template.
    * `output_parser`: (Optional) Hint on how to parse the output (e.g., 'python_code_block', 'json').
    * `review_points`: List of manual checks needed after generation.
    * `fallback_prompt_template`: (Optional) Path to template for retry on failure.
  * `manual_instructions`: (Present if `type == MANUAL`) Step-by-step instructions.
  * `script_details`: (Present if `type == AUTOMATED_SCRIPT`) Command or script path to run.
  * `output_artifact`: Path where the primary output should be saved (e.g., `happy_llm_cli/providers/base.py`).
  * `last_run`:
    * `timestamp`: ISO format timestamp.
    * `outcome`: (`SUCCESS`, `FAILURE`)
    * `llm_response`: (Optional) Raw LLM response snippet.
    * `cost_estimate`: (Optional) Token usage/cost.
  * `issues`: List of dictionaries for tracking errors:
    * `timestamp`: ISO format timestamp.
    * `type`: e.g., `GENERATION_ERROR`, `VALIDATION_FAIL`, `MANUAL_BLOCKER`.
    * `detail`: Description of the issue.
    * `resolution`: How it was/should be resolved (e.g., "Retried with fallback", "Manually edited code").

### 4.3. Orchestrator Script (`run.py`)

* **Language:** Python
* **Core Logic (Main Loop):**
    1. Load `runbook.yaml`.
    2. Find the first task with `status == READY`. If none, exit successfully.
    3. If a task has `status == ERROR`, print error info and exit (or prompt user).
    4. If a `READY` task is found:
        * Print task name and description.
        * Load the corresponding `task_detail_file`.
        * Mark task `RUNNING` in both files (save immediately).
        * **Execute based on `type`:**
            * `MANUAL`: Print `manual_instructions`. Wait for user confirmation (e.g., input `y` to continue, `e` to mark error, `s` to skip).
            * `AI_ASSISTED`:
                * Load `prompt_template`, populate with `input_context`.
                * Call OpenAI API function (see below).
                * Display generated output to user.
                * Print `review_points`.
                * Prompt user: Accept (mark `DONE`), Retry (potentially use `fallback_prompt_template`), Mark Error, Edit Manually (mark `DONE` but log manual edit).
            * `AUTOMATED_SCRIPT`: Execute the script. Check exit code. Mark `DONE` or `ERROR`.
        * **Update Status:** Based on execution outcome, update `status` in both files (`DONE`, `ERROR`, `SKIPPED`).
        * **Log:** Record action, outcome, timestamp, (optional) cost, errors in the log file.
        * If `DONE`, go back to step 2 to find the next `READY` task.
* **Helper Functions:**
  * `load_yaml`, `save_yaml`
  * `call_openai_api(prompt, model)`: Handles API interaction, returns response, potentially basic error handling (network issues).
  * `log_event(...)`
  * `check_dependencies(task_id, runbook_data)`: Verifies all dependencies are `DONE`. Update status to `READY` if applicable.

### 4.4. Logging

* **Format:** JSON Lines (JSONL) is recommended for easy parsing. Each line is a JSON object.
* **Content per Log Entry:**
  * `timestamp`
  * `task_id`
  * `event_type`: (`START_TASK`, `COMPLETE_TASK`, `ERROR_TASK`, `SKIP_TASK`, `AI_PROMPT_SENT`, `AI_RESPONSE_RECEIVED`, `MANUAL_ACTION`)
  * `status_change`: (Optional) e.g., `PENDING -> RUNNING`
  * `details`: (Optional) e.g., Error message, prompt snippet, model used, cost estimate, user confirmation.

### 4.5. Directory Structure Example

```
/happy-llm-cli/
├── run.py                     # Orchestrator script
├── runbook.yaml               # Master task flow
│
├── tasks/                     # Task Detail Files
│   ├── phase_0_summary.yaml
│   ├── task_1.1.1.yaml
│   ├── task_1.1.2.yaml
│   ├── ...
│   └── task_6.4.6.yaml
│
├── prompt_templates/          # Reusable prompt sections/files
│   ├── generate_abc.txt
│   ├── generate_test_mock.txt
│   └── generate_readme_section.txt
│
├── logs/                      # Execution logs
│   └── run_log.jsonl
│
├── outputs/                   # Store for generated artifacts (optional, code often goes direct to source)
│   └── generated_readme_draft.md
│
├── happy_llm_cli/             # Source code (managed by the tasks)
│   ├── __init__.py
│   ├── cli.py
│   │   ...
│
├── tests/                     # Test code (managed by the tasks)
│   │   ...
│
├── .env                       # API keys etc (ignored by git)
├── .env.example
├── pyproject.toml             # Project dependencies declared here
├── Containerfile
├── .gitignore
└── README.md                  # Final README (managed by tasks)
```

## 5. Workflow Loop (Solo Dev Perspective)

1. **Open Terminal** in the development container.
2. **Run the orchestrator**:
   • `python3 orchestration/run.py` (from project root)
   • `python3 -m orchestration.run`
   • (after `pip install -e .`) `happy-llm-orchestrate`
3. **Review:** The script prints the next `READY` task's details.
4. **Execute/Confirm:**
    * If `MANUAL`, perform the steps printed, then type `y` in the script prompt.
    * If `AI_ASSISTED`, review the generated prompt (optional step), let it run, review the output and review points, then type `y` (accept), `r` (retry), `e` (error), or `m` (accepted after manual edit).
    * If `AUTOMATED_SCRIPT`, observe execution.
5. **Script Updates:** The script updates the status in `runbook.yaml` and `tasks/<task_id>.yaml` and logs the action.
6. **Loop:** The script automatically looks for the next `READY` task.
7. **Handle Errors:** If a task is marked `ERROR`, the script stops and indicates the problematic task ID. Manually investigate `tasks/<task_id>.yaml` (check `issues`), fix the underlying problem (e.g., edit code, fix prompt template), update the `issues` section with resolution details, manually change the status back to `READY` in the YAML files, and re-run `./run.py`.
8. **Repeat** until no more `READY` tasks are found.

## 6. Implementation Steps (Initial Focus)

1. **Setup:** Create the directory structure (`tasks`, `logs`, `prompt_templates`). Create initial `runbook.yaml` and corresponding empty `tasks/*.yaml` files based *exactly* on the granular Phase 0-5 structure previously defined.
2. **YAML Utilities:** Implement helper functions in `run.py` to load/save YAML safely.
3. **Basic Orchestrator Logic:** Implement the core loop in `run.py` to find the next `READY` task based on status and `depends_on`. Implement basic status updates (`PENDING` -> `RUNNING` -> `DONE`/`ERROR`).
4. **Manual Task Handler:** Implement the logic for `type: MANUAL`.
5. **Logging:** Add basic file logging for task start/end/error.
6. **AI Task Handler (Core):**
    * Implement template loading/population.
    * Implement `call_openai_api` function using the `openai` library.
    * Integrate into the `AI_ASSISTED` task execution flow with user review prompts.
7. **Error Handling:** Implement basic error state handling (script stops, requires manual YAML edit to retry). Add `issues` tracking in task detail YAML.
8. **Refine:** Add fallback prompt logic, automated script handler, more detailed logging (cost), dependency checking for setting `READY` status.

## 7. Tooling Suggestions

* **Python:** Core language.
* **PyYAML:** For reading/writing YAML files.
* **openai:** Official library for API calls.
* **Typer / argparse:** (Optional) For adding command-line arguments to `run.py` (e.g., `./run.py --start-from <task_id>`).
* **Jinja2:** (Optional) For more complex prompt templating.
* **Git:** For version control of the runbook, task files, prompts, and generated code.

## 8. Solo Developer Considerations

This approach is tailored for a solo developer by:

* **Minimizing Setup:** Relies on simple file structures and a single orchestrator script initially.
* **Manual Control:** The developer is always in the loop for AI outputs and error resolution.
* **Linearity:** Follows a clear step-by-step process defined in the editable `runbook.yaml`.
* **Transparency:** YAML files make the state and task details easily visible and modifiable.
* **Incremental Build:** Start with manual tasks and basic AI calls, then layer in more automation or sophisticated error handling later.

---

This plan provides a blueprint for a practical, manageable system to orchestrate your development tasks using the structure you've already defined. It prioritizes getting a working loop running quickly, allowing you to iteratively enhance it.
