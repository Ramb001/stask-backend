import asyncio
import logging

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
            filter=f"workers.tg_id='{user_id}'",
            expand="owner,workers",
        )

        user = await fetch_user(user_id, PB, client)

        if len(organizations_["items"]):
            organizations = []
            for org in organizations_["items"]:
                organizations.append(
                    {
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
