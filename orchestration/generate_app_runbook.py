#!/usr/bin/env python3
"""
Generate application build tasks in the orchestrator runbook based on planning files.

This script reads YAML files under docs/planning/ (phase0.yaml through phase5.yaml)
and appends corresponding task entries to orchestration/runbook.yaml,
then creates per-task detail files under orchestration/tasks/.
Use this once to bootstrap the application build workflow.
"""
import yaml
from pathlib import Path
import argparse


def main():
    base_dir = Path(__file__).parent
    runbook_path = base_dir / 'runbook.yaml'
    tasks_dir = base_dir / 'tasks'
    planning_dir = base_dir.parent / 'docs' / 'planning'

    # Load existing runbook
    if not runbook_path.exists():
        print(f"Runbook not found: {runbook_path}")
        return
    with open(runbook_path) as f:
        runbook = yaml.safe_load(f) or {}
    tasks = runbook.setdefault('tasks', [])
    existing_ids = {t.get('id') for t in tasks}

    # Parse optional phase selection
    parser = argparse.ArgumentParser(
        description="Generate application build tasks from planning files"
    )
    parser.add_argument(
        '--phases', '-p', nargs='+', type=int, default=[0],
        help="Phase numbers to generate (0-5). Default: 0"
    )
    args = parser.parse_args()
    selected = set(args.phases)

    # Process each phase planning file in order
    for pf in sorted(planning_dir.glob('phase*.yaml')):
        # Determine phase index from filename, e.g., 'phase0.yaml' -> 0
        try:
            phase_idx = int(pf.stem.replace('phase', ''))
        except ValueError:
            continue
        if phase_idx not in selected:
            continue
        # Load planning file
        with open(pf) as f_pl:
            planning = yaml.safe_load(f_pl) or {}
        subtasks = planning.get('subtasks', []) or []
        for st in subtasks:
            pid = st.get('id')  # e.g. '1.1.1'
            if not pid:
                continue
            task_id = f"app_{pid}"
            if task_id in existing_ids:
                continue
            # Determine type and dependencies
            ai_assisted = bool(st.get('ai_assisted'))
            task_type = 'AI_ASSISTED' if ai_assisted else 'MANUAL'
            deps = st.get('dependencies') or []
            if not deps:
                # start after orchestrator tasks complete
                deps = ['orchestrate_8_refine']
            else:
                deps = [f"app_{d}" for d in deps]
            # Append runbook entry
            entry = {
                'depends_on': deps,
                'id': task_id,
                'name': st.get('name'),
                'status': 'PENDING',
                'task_detail_file': f"tasks/{task_id}.yaml",
                'type': task_type,
            }
            tasks.append(entry)
            existing_ids.add(task_id)
            # Build detail file content
            detail = {
                'id': task_id,
                'name': st.get('name'),
                'status': 'PENDING',
                'type': task_type,
                'depends_on': deps,
            }
            # Add instructions or AI details
            if ai_assisted:
                ai = {}
                model = st.get('model')
                if model:
                    ai['model'] = model
                prompt = st.get('prompt_template') or st.get('details')
                if prompt:
                    ai['prompt'] = prompt.strip()
                detail['ai_details'] = ai
            else:
                details = st.get('details', '')
                # use details block as single instruction item
                detail['manual_instructions'] = [details.strip()]
            # Include outputs if present
            if 'outputs' in st:
                detail['outputs'] = st.get('outputs')
            # Write detail YAML
            out_path = tasks_dir / f"{task_id}.yaml"
            with open(out_path, 'w') as f:
                yaml.safe_dump(detail, f, sort_keys=False)
            print(f"Created task detail: {out_path}")

    # Save updated runbook
    with open(runbook_path, 'w') as f:
        yaml.safe_dump(runbook, f, sort_keys=False)
    print(f"Updated runbook: {runbook_path}")


if __name__ == '__main__':  # pragma: no cover
    main()