#!/usr/bin/env python3
"""
Orchestration script for managing and executing development tasks via a YAML-defined runbook.

This script provides utilities to load and save YAML files, evaluate task dependencies,
and iterate through tasks marked as READY in the runbook, updating their status as they execute.
"""

import yaml
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
try:
    import openai
except ImportError:
    openai = None
import subprocess
from typing import Tuple
import argparse

BASE_DIR = Path(__file__).parent
RUNBOOK_PATH = BASE_DIR / 'runbook.yaml'
LOG_DIR = BASE_DIR / 'logs'
LOG_PATH = LOG_DIR / 'run_log.jsonl'

# Cost estimation per 1,000 tokens (USD). Override via COST_PER_1K_TOKENS env var.
COST_PER_1K_TOKENS = float(os.getenv("COST_PER_1K_TOKENS", "0.002"))

def estimate_cost(tokens: int) -> float:
    """Estimate USD cost given total token count."""
    try:
        return round((tokens or 0) / 1000.0 * COST_PER_1K_TOKENS, 6)
    except Exception:
        return 0.0

def load_yaml(path):
    """
    Load a YAML file and return its contents as a dict.

    Parameters:
        path (str or Path): Path to the YAML file.

    Returns:
        dict: Parsed YAML data (empty dict if file is empty).

    Exits the script on file not found or parse errors.
    """
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Error: YAML file not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {path}: {e}")
        sys.exit(1)

def save_yaml(data, path):
    """
    Save a dict to a YAML file.

    Parameters:
        data (dict): Data to serialize.
        path (str or Path): Destination file path.

    Exits the script on any file write errors.
    """
    try:
        with open(path, 'w') as f:
            yaml.safe_dump(data, f)
    except Exception as e:
        print(f"Error writing YAML file {path}: {e}")
        sys.exit(1)

def get_task_by_id(runbook, task_id):
    """
    Retrieve a task dict from the runbook by its ID.

    Parameters:
        runbook (dict): The loaded runbook data.
        task_id (str): The ID of the task to find.

    Returns:
        dict or None: Task dict if found, else None.
    """
    for t in runbook.get('tasks', []):
        if t.get('id') == task_id:
            return t
    return None

def dependencies_met(task, runbook):
    """
    Check if all dependencies of a task are in 'DONE' status.

    Parameters:
        task (dict): Task entry from runbook.
        runbook (dict): Runbook data containing all tasks.

    Returns:
        bool: True if all dependencies are done, False otherwise.
    """
    """
    Check if all dependencies of a task are met (DONE or SKIPPED).
    """
    for dep in task.get('depends_on', []):
        dep_task = get_task_by_id(runbook, dep)
        # Treat SKIPPED and DONE as satisfied dependencies
        if not dep_task or dep_task.get('status') not in ('DONE', 'SKIPPED'):
            return False
    return True

def refresh_ready_tasks(runbook):
    """
    Promote tasks from 'PENDING' to 'READY' if their dependencies are met.

    Parameters:
        runbook (dict): The loaded runbook data.
    """
    updated = False
    for t in runbook.get('tasks', []):
        if t.get('status') == 'PENDING' and dependencies_met(t, runbook):
            t['status'] = 'READY'
            updated = True
    if updated:
        save_yaml(runbook, RUNBOOK_PATH)

def get_next_ready_task(runbook):
    """
    Retrieve the next task that is ready to run.

    Parameters:
        runbook (dict): The loaded runbook data.

    Returns:
        dict or None: Next ready task dict, or None if none available.
    """
    for t in runbook.get('tasks', []):
        if t.get('status') == 'READY' and dependencies_met(t, runbook):
            return t
    return None

def update_task_status(runbook, task, new_status):
    """
    Update the status of a task in both runbook and its detail file.

    Parameters:
        runbook (dict): The loaded runbook data.
        task (dict): The task entry to update.
        new_status (str): New status value ('RUNNING', 'DONE', etc.).
    """
    task['status'] = new_status
    save_yaml(runbook, RUNBOOK_PATH)
    detail_path = BASE_DIR / task.get('task_detail_file')
    detail = load_yaml(detail_path)
    detail['status'] = new_status
    save_yaml(detail, detail_path)

def log_event(task_id, event_type, status_change=None, details=None):
    """
    Append a log entry to the JSONL log file.
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # Use timezone-aware UTC timestamp with 'Z' suffix
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'task_id': task_id,
        'event_type': event_type,
    }
    if status_change:
        entry['status_change'] = status_change
    if details:
        entry['details'] = details
    try:
        with open(LOG_PATH, 'a') as lf:
            lf.write(json.dumps(entry) + '\n')
    except Exception as e:
        print(f"Error writing log file {LOG_PATH}: {e}")

def call_openai_api(prompt: str, model: str) -> Tuple[str, dict]:
    """
    Send a prompt to OpenAI chat completion API and return the assistant's response text and usage info.
    Returns:
        tuple[str, dict]: (response text, usage information such as token counts).
    """
    if openai is None:
        print("Error: openai library is not installed. Please install it (pip install openai).")
        return "", {}
    # Ensure API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return "", {}
    try:
        # Instantiate new OpenAI client using the Responses API
        client = openai.OpenAI(api_key=api_key)
        # Send request and get a unified Response
        resp = client.responses.create(
            model=model,
            input=prompt,
        )
        # Extract text output
        content = getattr(resp, 'output_text', '') or ''
        # Extract usage information if available
        if hasattr(resp, 'usage') and resp.usage:
            usage = {
                'input_tokens': getattr(resp.usage, 'input_tokens', None),
                'output_tokens': getattr(resp.usage, 'output_tokens', None),
                'total_tokens': getattr(resp.usage, 'total_tokens', None),
            }
        else:
            usage = {}
        return content, usage
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "", {}
 
def record_issue(detail_path: Path, issue_type: str, detail: str) -> None:
    """
    Append an issue entry to the task detail YAML issues list.
    """
    try:
        data = load_yaml(detail_path)
        issues = data.get('issues', []) or []
        issues.append({
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'type': issue_type,
            'detail': detail,
        })
        data['issues'] = issues
        save_yaml(data, detail_path)
    except Exception as e:
        print(f"Error recording issue in {detail_path}: {e}")

def main(start_from=None):
    """
    Main entry point: execute tasks in the runbook sequentially.

    Loads the runbook, promotes ready tasks, and loops until all are processed.
    """
    runbook = load_yaml(RUNBOOK_PATH)
    # Handle start-from option to skip ahead
    if start_from:
        tasks = runbook.get('tasks', [])
        ids = [t.get('id') for t in tasks]
        if start_from not in ids:
            print(f"Start-from ID '{start_from}' not found in runbook.")
            sys.exit(1)
        start_index = ids.index(start_from)
        for idx, t in enumerate(tasks):
            if idx < start_index:
                t['status'] = 'SKIPPED'
            elif idx == start_index:
                t['status'] = 'READY'
            else:
                if t.get('status') != 'DONE':
                    t['status'] = 'PENDING'
        save_yaml(runbook, RUNBOOK_PATH)
    # Check for any tasks in ERROR state before proceeding
    for t in runbook.get('tasks', []):
        if t.get('status') == 'ERROR':
            print(f"Task {t.get('id')} is in ERROR state. Please resolve issues in '{t.get('task_detail_file')}' and set status back to READY.")
            sys.exit(1)
    while True:
        refresh_ready_tasks(runbook)
        task = get_next_ready_task(runbook)
        if not task:
            print("No READY tasks. Exiting.")
            break
        print(f"Next task: {task.get('id')} - {task.get('name')}")
        # Mark as RUNNING and log
        prev_status = task.get('status')
        update_task_status(runbook, task, 'RUNNING')
        print(f"Marked {task.get('id')} as RUNNING")
        log_event(task.get('id'), 'START_TASK', f"{prev_status}->RUNNING")

        # Load task detail for handler logic
        detail_path = BASE_DIR / task.get('task_detail_file')
        detail = load_yaml(detail_path)
        task_type = task.get('type')

        if task_type == 'MANUAL':
            # Display manual instructions and prompt for user action
            instructions = detail.get('manual_instructions', []) or []
            print("\nManual task instructions:")
            for instr in instructions:
                print(f"  - {instr}")
            choice = ''
            while choice not in ('y', 'e', 's'):
                choice = input("Enter choice [y=done, e=error, s=skip]: ").strip().lower()
            new_status = 'DONE' if choice == 'y' else ('SKIPPED' if choice == 's' else 'ERROR')
            update_task_status(runbook, task, new_status)
            print(f"Marked {task.get('id')} as {new_status}")
            # Log completion or error
            evt = 'COMPLETE_TASK' if new_status == 'DONE' else 'ERROR_TASK'
            log_event(task.get('id'), evt, f"RUNNING->{new_status}")
            # Record issue if manual error
            if new_status == 'ERROR':
                detail_path = BASE_DIR / task.get('task_detail_file')
                record_issue(detail_path, 'USER_MARKED_ERROR', 'Manual task marked as error')
            # Process one task at a time; exit after handling
            break
        elif task_type == "AUTOMATED_SCRIPT":
            # Automated script task: execute shell command or script
            script_info = detail.get("script_details", {}) or {}
            command = script_info.get("command")
            if not command:
                print("No 'command' specified for AUTOMATED_SCRIPT task.")
                new_status = "ERROR"
            else:
                print(f"Executing script command: {command}")
                try:
                    result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True)
                    print("STDOUT:\n", result.stdout)
                    if result.stderr:
                        print("STDERR:\n", result.stderr)
                    new_status = "DONE" if result.returncode == 0 else "ERROR"
                except Exception as e:
                    print(f"Script execution error: {e}")
                    new_status = "ERROR"
            update_task_status(runbook, task, new_status)
            evt = "COMPLETE_TASK" if new_status == "DONE" else "ERROR_TASK"
            # Include return code and zero cost for automated scripts
            details = {
                "returncode": result.returncode if 'result' in locals() else None,
                "cost_usd": 0.0
            }
            log_event(task.get("id"), evt, f"RUNNING->{new_status}", details)
            if new_status == "ERROR":
                detail_path = BASE_DIR / task.get("task_detail_file")
                record_issue(detail_path, "SCRIPT_ERROR", str(details.get("returncode")))
            break
        elif task_type == "AI_ASSISTED":
            # AI-assisted task: send prompt, review, and status update with retry/fallback
            ai_det = detail.get("ai_details", {}) or {}
            prompt = ai_det.get("prompt", "")
            fallback_prompt = ai_det.get("fallback_prompt")
            model = ai_det.get("model")
            while True:
                print("\nSending prompt to OpenAI API...")
                result, usage = call_openai_api(prompt, model)
                print("\nLLM response:\n", result)
                review = ai_det.get("review_points", []) or []
                if review:
                    print("\nReview points:")
                    for rp in review:
                        print(f"  - {rp}")
                choice = ""
                while choice not in ("y", "r", "e", "m"):
                    choice = input("Enter choice [y=accept, r=retry, e=error, m=manual]: ").strip().lower()
                if choice in ("y", "m"):
                    new_status = "DONE"
                    break
                elif choice == "e":
                    new_status = "ERROR"
                    break
                else:
                    # retry
                    if fallback_prompt:
                        prompt = fallback_prompt
                        print("\nRetrying with fallback prompt...")
                    else:
                        print("\nRetrying with original prompt...")
                    continue
            update_task_status(runbook, task, new_status)
            evt = "COMPLETE_TASK" if new_status == "DONE" else "ERROR_TASK"
            # Include usage and cost estimation in log details
            cost = estimate_cost(usage.get("total_tokens") if isinstance(usage, dict) else 0)
            log_event(
                task.get("id"),
                evt,
                f"RUNNING->{new_status}",
                {"response": result, "usage": usage, "cost_usd": cost}
            )
            if new_status == "ERROR":
                detail_path = BASE_DIR / task.get("task_detail_file")
                record_issue(detail_path, "AI_RESPONSE_REJECTED", result)
            break
        else:
            # Stub for other task types: mark as DONE
            update_task_status(runbook, task, "DONE")
            print(f"Marked {task.get('id')} as DONE")
            log_event(task.get("id"), "COMPLETE_TASK", "RUNNING->DONE")
            break

def cli():
    """Command-line entry point to parse arguments and invoke main()."""
    parser = argparse.ArgumentParser(description='Orchestration script for managing and executing tasks.')
    parser.add_argument('--start-from', dest='start_from', help='Task ID to start from', default=None)
    args = parser.parse_args()
    return main(start_from=args.start_from)

if __name__ == '__main__':
    cli()