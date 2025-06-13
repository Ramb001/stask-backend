import asyncio
import logging
import uuid

import uvicorn

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models import (
    DeleteOrganization,
    DeleteWorker,
    LeaveOrganization,
    TaskDecomposition,
    UpdateStatus,
    UpdateUserInfo,
    Goal,
    TaskApproval,
    ChatMessage,
)
from src.services.ai_agent import decompose_goal
from src.helpers import fetch_organization, fetch_tasks_lenght, fetch_user
from src.constants import PB, PocketbaseCollections


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = FastAPI()
loop = asyncio.get_event_loop()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get-organizations")
async def get_organizations(user_id: str):
    async with aiohttp.ClientSession() as client:
        organizations_ = await PB.fetch_records(
            PocketbaseCollections.ORGANIZATIONS,
            client,
            filter=f"owner.tg_id='{user_id}'||workers.tg_id?='{user_id}'",
            expand="owner",
        )
        user = await fetch_user(user_id, PB, client)

        if len(organizations_["items"]):
            organizations = []
            for org in organizations_["items"]:
                organizations.append(
                    {
                        "id": org["id"],
                        "name": org["name"],
                        "user_status": (
                            "Owner"
                            if org["expand"]["owner"]["id"] == user["id"]
                            else "Worker"
                        ),
                    }
                )
            return organizations
        else:
            return []


@app.get("/get-tasks")
async def get_tasks(organization_id: str):
    async with aiohttp.ClientSession() as client:
        tasks = await PB.fetch_records(
            PocketbaseCollections.TASKS,
            client,
            filter=f"organization.id='{organization_id}'",
            expand="workers",
        )

        resp = []
        for task in tasks["items"]:
            temp = {
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "deadline": task["deadline"],
                "requested": task["requested"],
                "verified": task["verified"],
            }

            workers = []
            if "expand" in task:
                for worker in task["expand"]["workers"]:
                    workers.append(
                        {
                            "name": (
                                worker["name"]
                                if worker["name"] != ""
                                else worker["username"]
                            ),
                            "value": "name" if worker["name"] != "" else "username",
                        }
                    )

            temp["workers"] = workers
            resp.append(temp)

        return resp


@app.post("/change-task-status")
async def change_task_status(request: UpdateStatus):
    async with aiohttp.ClientSession() as client:
        if request.status != "done":
            await PB.update_record(
                PocketbaseCollections.TASKS,
                request.task_id,
                client,
                status=request.status,
                requestes=False,
                verified=False,
            )
        elif request.status == "done":
            await PB.update_record(
                PocketbaseCollections.TASKS,
                request.task_id,
                client,
                status=request.status,
                requested=True if request.user_status == "Worker" else False,
                verified=True if request.user_status == "Owner" else False,
            )


@app.get("/get-workers")
async def get_workers(organization_id: str):
    async with aiohttp.ClientSession() as client:
        workers = await PB.fetch_records(
            PocketbaseCollections.ORGANIZATIONS,
            client,
            filter=f"id='{organization_id}'",
            expand="workers",
        )

        return [
            {
                "id": worker["id"],
                "name": worker["name"],
                "username": worker["username"],
                "tg_id": worker["tg_id"],
                "chat_id": worker["chat_id"],
            }
            for worker in workers["items"][0]["expand"]["workers"]
        ]


@app.get("/get-requests")
async def get_requests(organization_id: str):
    async with aiohttp.ClientSession() as client:
        requested_tasks = await PB.fetch_records(
            PocketbaseCollections.TASKS,
            client,
            filter=f"organization.id='{organization_id}'&&status='done'&&requested=true",
            expand="workers",
        )

        resp = []

        for task in requested_tasks["items"]:
            temp = {
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "deadline": task["deadline"],
            }

            workers = []
            for worker in task["expand"]["workers"]:
                workers.append(
                    {
                        "name": (
                            worker["name"]
                            if worker["name"] != ""
                            else worker["username"]
                        ),
                        "value": "name" if worker["name"] != "" else "username",
                    }
                )

            temp["workers"] = workers
            resp.append(temp)

        return resp


@app.get("/get-organization-info")
async def get_orgnization_info(organization_id: str):
    async with aiohttp.ClientSession() as client:
        organization_ = await PB.fetch_records(
            PocketbaseCollections.ORGANIZATIONS,
            client,
            filter=f"id='{organization_id}'",
            expand="workers, owner",
        )

        if len(organization_["items"]):
            organization = organization_["items"][0]
            resp = {
                "name": organization["name"],
                "owner": (
                    organization["expand"]["owner"]["name"]
                    if len(organization["expand"]["owner"]["name"]) != 0
                    else organization["expand"]["owner"]["username"]
                ),
                "ref_link": organization["ref_link"],
            }
            workers = []
            if organization["expand"]["workers"]:
                for worker in organization["expand"]["workers"]:
                    workers.append(
                        {
                            "id": worker["id"],
                            "name": (
                                worker["name"]
                                if worker["name"] != ""
                                else worker["username"]
                            ),
                            "value": "name" if worker["name"] != "" else "username",
                        }
                    )
            resp["workers"] = workers
            resp["tasks"] = await fetch_tasks_lenght(organization_id, PB, client)

            return resp
        else:
            return []


@app.post("/delete-worker")
async def delete_worker(request: DeleteWorker):
    async with aiohttp.ClientSession() as client:
        organization = await fetch_organization(request.organization_id, PB, client)

        if organization["owner"] == request.worker_id:
            return False

        else:
            organization["workers"].remove(request.worker_id)

            await PB.update_record(
                PocketbaseCollections.ORGANIZATIONS,
                request.organization_id,
                client,
                workers=organization["workers"],
            )


@app.get("/get-user-name")
async def get_user_name(user_id: str):
    async with aiohttp.ClientSession() as client:
        user = await fetch_user(user_id, PB, client)
        return user["name"]


@app.post("/update-user-name")
async def update_user_name(request: UpdateUserInfo):
    async with aiohttp.ClientSession() as client:
        user = await fetch_user(request.user_id, PB, client)
        await PB.update_record(
            PocketbaseCollections.USERS, user["id"], client, name=request.new_name
        )


@app.post("/leave-organization")
async def leave_organization(request: LeaveOrganization):
    async with aiohttp.ClientSession() as client:
        organization = await fetch_organization(request.organization_id, PB, client)
        user = await fetch_user(request.user_id, PB, client)

        organization["workers"].remove(user["id"])
        await PB.update_record(
            PocketbaseCollections.ORGANIZATIONS,
            request.organization_id,
            client,
            workers=organization["workers"],
        )


@app.post("/delete-organization")
async def delete_organization(request: DeleteOrganization):
    async with aiohttp.ClientSession() as client:
        await PB.delete_record(
            PocketbaseCollections.ORGANIZATIONS, request.organization_id, client
        )


@app.post("/process-goal")
async def process_goal(goal: Goal):
    try:
        async with aiohttp.ClientSession() as client:
            task_decomposition = await decompose_goal(
                goal.message, goal.organization_id, goal.department, client
            )

        return task_decomposition
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve-tasks")
async def approve_tasks(data: TaskApproval):
    try:
        async with aiohttp.ClientSession() as client:
            for task in data.tasks:
                department = await PB.fetch_records(
                    PocketbaseCollections.DEPARTMENTS,
                    client,
                    filter=f"company.id='{data.organization_id}'&name='{task.department}'",
                )
                await PB.add_record(
                    PocketbaseCollections.TASKS,
                    client,
                    title=task.title,
                    description=task.description,
                    organization=data.organization_id,
                    suborganization=department["items"][0]["id"],
                    creator=data.user_id,
                    workers=task.workers,
                    deadline=task.deadline.strftime("%d/%m/%Y"),
                    status="not_started",
                )

            return {"message": "Tasks added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-departments")
async def get_organization_departments(organization_id: str):
    async with aiohttp.ClientSession() as client:
        org_data = await PB.fetch_records(
            PocketbaseCollections.DEPARTMENTS,
            client,
            filter=f'company.id="{organization_id}"',
        )
        if not org_data["items"]:
            return []
        return [{"name": dept["name"], "id": dept["id"]} for dept in org_data["items"]]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
