#!/usr/bin/env python3
"""
Roadmap loop using Anthropic's Python SDK.

Requires:
pip install anthropic pyyaml
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import yaml
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent
TASKS_FILE = ROOT / "tasks.yaml"
LOG_DIR = ROOT / "docs" / "work-log"
CHANGELOG = ROOT / "docs" / "changelog.md"

MODEL = "claude-3-7-sonnet-latest"
client = Anthropic()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Task:
    id: str
    title: str
    status: str = "todo"
    depends_on: List[str] = field(default_factory=list)
    goal: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    validation_commands: List[str] = field(default_factory=list)


def load_tasks() -> List[Task]:
    data = yaml.safe_load(TASKS_FILE.read_text(encoding="utf-8")) or []
    return [Task(**item) for item in data]


def save_tasks(tasks: List[Task]) -> None:
    TASKS_FILE.write_text(
        yaml.safe_dump([task.__dict__ for task in tasks], sort_keys=False),
        encoding="utf-8",
    )


def next_task(tasks: List[Task]) -> Task | None:
    for task in tasks:
        if task.status == "todo" and all(
            next(x for x in tasks if x.id == dep).status == "done"
            for dep in task.depends_on
        ):
            return task
    return None


def validate(task: Task) -> bool:
    results = []
    for cmd in task.validation_commands:
        print(f"> {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=ROOT)
        results.append(result.returncode == 0)
    return all(results) if results else True


def log(task: Task, notes: str = "") -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{task.id}.md"
    path.write_text(
        f"""# {task.id}

## Status
{task.status}

## Notes
{notes}

## Timestamp
{utc_now()}
""",
        encoding="utf-8",
    )

    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    if not CHANGELOG.exists():
        CHANGELOG.write_text("# Changelog\n\n", encoding="utf-8")
    with CHANGELOG.open("a", encoding="utf-8") as f:
        f.write(f"- {task.id}: {task.status} ({utc_now()})\n")


def run_agent(task: Task) -> str:
    prompt = f"""
You are implementing exactly one roadmap task.

Task ID: {task.id}
Title: {task.title}

Goal:
{task.goal}

Acceptance Criteria:
{chr(10).join("- " + item for item in task.acceptance_criteria) if task.acceptance_criteria else "- n/a"}

Rules:
- Work only on this task
- Keep the change set minimal
- Do not start another task
- Explain what you would change and why
- End with a concise implementation summary
""".strip()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    text_blocks = []
    for block in response.content:
        if getattr(block, "type", "") == "text":
            text_blocks.append(block.text)
    output = "\n".join(text_blocks)
    print("\n--- AGENT OUTPUT ---\n")
    print(output)
    print("\n--------------------\n")
    return output


def loop(limit: int = 5) -> None:
    tasks = load_tasks()

    for _ in range(limit):
        task = next_task(tasks)
        if not task:
            print("No tasks left.")
            return

        print(f"\n=== {task.id}: {task.title} ===")
        task.status = "in_progress"
        save_tasks(tasks)

        agent_output = run_agent(task)

        if validate(task):
            task.status = "done"
            log(task, f"validated successfully\n\nAgent output:\n{agent_output}")
            print("DONE")
        else:
            task.status = "blocked"
            log(task, f"validation failed\n\nAgent output:\n{agent_output}")
            print("BLOCKED")
            save_tasks(tasks)
            return

        save_tasks(tasks)
        print("\nClear context before the next task.\n")


if __name__ == "__main__":
    loop()
