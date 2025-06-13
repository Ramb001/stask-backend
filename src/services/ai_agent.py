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
    return [dept["name"] for dept in org_data["items"]]


async def decompose_goal(
    message: str, organization_id: str, department: str, client
) -> TaskDecomposition:
    departments = []
    if department.lower() == "general":
        departments = await get_organization_departments(organization_id, client)

    system_prompt = """
You are an AI business analyst and project manager. Your task is to break down a business goal into specific, actionable tasks considering the department's specifics.

IMPORTANT: All task titles and descriptions MUST be in Russian language.

If the department is "general":
- Form tasks relevant to the entire company.
- For each task, include all departments involved in execution using the "departments" field — an array of department names like ["IT", "HR", "Маркетинг"].
- In the description, clearly explain the role of each department in completing the task.

If the department is specific (e.g., "IT"):
- Use professional terminology relevant to the given department.
- Assign all tasks only to that department, and set "departments" as an array with one value: ["IT"].

Each task must follow this structure:
- id — unique identifier: "task-001", "task-002", ...
- title — short task title in Russian
- description — 2–3 sentences in Russian. For "general", include guidance per department.
- deadline — realistic deadline (format YYYY-MM-DD)
- recommended_executors — estimated number of executors
- priority — one of: "high", "medium", "low"
- depends_on — array of task ids it depends on (can be empty)
- departments — array of departments involved in execution of the task

Return a single valid JSON object in this exact format (in Russian language):
{
  "tasks": [
    {
      "id": "task-001",
      "title": "...",
      "description": "...",
      "deadline": "...",
      "recommended_executors": ...,
      "priority": "...",
      "depends_on": [],
      "departments": ["..."]
    },
    ...
  ]
}
"""

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
                {
                    "id": task_data["id"],
                    "title": task_data["title"],
                    "description": task_data["description"],
                    "status": "pending",
                    "created_at": datetime.now(),
                    "deadline": task_data["deadline"],
                    "recommended_executors": task_data["recommended_executors"],
                    "priority": task_data["priority"],
                    "depends_on": task_data["depends_on"],
                }
            )

        return {"tasks": tasks}
