import asyncio

import aiohttp

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
