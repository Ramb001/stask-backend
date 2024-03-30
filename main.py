import asyncio
import logging

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.models import UpdateStatus
from src.helpers import fetch_user
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


@app.get("/get_organizations")
async def get_organizations(user_id: str):
    async with aiohttp.ClientSession() as client:
        organizations_ = await PB.fetch_records(
            PocketbaseCollections.ORGANIZATIONS,
            client,
            filter=f"workers.tg_id?='{user_id}'",
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
            filter=f"id='{organization_id}'",
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
