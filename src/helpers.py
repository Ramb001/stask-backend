import asyncio
from asyncio import tasks

import aiohttp
from collections import Counter

from src.constants import PocketbaseCollections
from src.pocketbase import Pocketbase

loop = asyncio.get_event_loop()


async def fetch_user(
    tg_id: int, pb: Pocketbase, client: aiohttp.ClientSession, **api_params
):
    users = await pb.fetch_records(
        PocketbaseCollections.USERS, client, filter=f"(tg_id='{tg_id}')", **api_params
    )
    return users["items"][0]


async def fetch_organization(
    organization_id: str, pb: Pocketbase, client: aiohttp.ClientSession, **api_params
):
    organizations = await pb.fetch_records(
        PocketbaseCollections.ORGANIZATIONS,
        client,
        filter=f"(id='{organization_id}')",
        **api_params,
    )
    return organizations["items"][0]


async def fetch_tasks_lenght(
    organization_id: str, pb: Pocketbase, client: aiohttp.ClientSession, **api_params
):
    tasks = await pb.fetch_records(
        PocketbaseCollections.TASKS,
        client,
        filter=f"(organization.id='{organization_id}')",
        **api_params,
    )

    if len(tasks["items"]):
        return Counter(task["status"] for task in tasks["items"])
