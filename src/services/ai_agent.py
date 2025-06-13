import os
import json
import httpx
from typing import List
from datetime import datetime

from ..models import Task, TaskDecomposition
from ..constants import PB, PocketbaseCollections

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/o4-mini")


async def get_organization_departments(organization_id: str, client) -> List[str]:
    org_data = await PB.fetch_records(
        PocketbaseCollections.DEPARTMENTS,
        client,
        filter=f"company.id='{organization_id}'",
    )
    if not org_data["items"]:
        return []
    return [
        dept["name"]
        for dept in org_data["items"][0].get("expand", {}).get("departments", [])
    ]


async def decompose_goal(
    message: str, organization_id: str, department: str, client
) -> TaskDecomposition:
    departments = []
    if department.lower() == "general":
        departments = await get_organization_departments(organization_id, client)

    system_prompt = """You are an AI business analyst and project manager. Your task is to break down a business goal into specific, actionable tasks considering the department's specifics.

IMPORTANT: All task titles and descriptions MUST be in Russian language.

If the department is "general", form tasks relevant to the entire company, explaining how each task relates to different departments' work. Tasks should be structured, have realistic deadlines, priorities, and dependencies, as well as recommendations on the number of executors.

Form clear, concise, but informative task descriptions in Russian that will help teams quickly understand what needs to be done and how to distribute the work.

Requirements:
1. If department is specific, break down the goal into tasks using profile-specific terminology and approaches.
2. If department is "general", form tasks for the entire company with explanations for each department.
3. Break tasks into logical steps (approximately 3-10 working days per task).
4. For each task specify:
   - id - unique identifier in "task-001", "task-002" format
   - title - task name in Russian
   - description - 2-3 sentences in Russian explaining essence and tips (for "general" department - with explanations for each department)
   - deadline - realistic deadline (YYYY-MM-DD)
   - recommended_executors - number of executors
   - priority - "high", "medium", "low"
   - depends_on - array of task ids this task depends on (can be empty)

Example of expected output format (but with Russian text):
[
  {
    "id": "task-001",
    "title": "Название задачи на русском",
    "description": "Описание задачи на русском языке. Дополнительные детали и рекомендации.",
    "deadline": "2024-04-20",
    "recommended_executors": 2,
    "priority": "high",
    "depends_on": []
  }
]

Respond with a strict JSON array of tasks."""

    input_data = {
        "goal": message,
        "department": department,
        "language": "Russian",
    }
    if departments:
        input_data["departments_list"] = departments

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(input_data)},
                ],
                "response_format": {"type": "json_object"},
            },
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.text}")

        result = response.json()
        tasks_data = json.loads(result["choices"][0]["message"]["content"])
        if isinstance(tasks_data, dict) and "tasks" in tasks_data:
            tasks_data = tasks_data["tasks"]

        tasks = []
        for task_data in tasks_data:
            tasks.append(
                Task(
                    id=task_data["id"],
                    title=task_data["title"],
                    description=task_data["description"],
                    status="pending",
                    created_at=datetime.now(),
                    goal_id="",
                    deadline=task_data["deadline"],
                    recommended_executors=task_data["recommended_executors"],
                    priority=task_data["priority"],
                    depends_on=task_data["depends_on"],
                )
            )

        return TaskDecomposition(goal_id="", tasks=tasks)
