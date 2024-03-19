import asyncio
import os
import time
from urllib.parse import urlencode

import aiohttp


class Pocketbase:
    def __init__(self, base_url: str):
        self.__base_url = base_url
        self.__token = None
        self.__token_update_time = 0
        self.__lock = asyncio.Lock()

    async def __get_headers(self, client: aiohttp.ClientSession):
        await self.__auth(client)
        return {"Authorization": f"Bearer {self.__token}"}

    async def __auth(self, client: aiohttp.ClientSession):
        async with self.__lock:
            if time.time() - self.__token_update_time < 1209500:
                return
            async with client.post(
                self.__base_url + "/api/admins/auth-with-password",
                json={
                    "identity": os.getenv("POCKETBASE_ADMIN_EMAIL"),
                    "password": os.getenv("POCKETBASE_ADMIN_PASSWORD"),
                },
            ) as resp:
                if resp.status != 200:
                    raise aiohttp.ClientError("Failed to auth")
                d = await resp.json()
                self.__token_update_time = time.time()
                self.__token = d["token"]

    async def fetch_records(
        self, collection_name: str, client: aiohttp.ClientSession, **api_params
    ):
        headers = await self.__get_headers(client)
        async with client.get(
            f"{self.__base_url}/api/collections/{collection_name}/records?"
            + urlencode(api_params),
            headers=headers,
        ) as resp:
            return await resp.json()

    async def update_record(
        self,
        collection_name: str,
        record_id: str,
        client: aiohttp.ClientSession,
        **api_params,
    ):
        headers = await self.__get_headers(client)
        async with client.patch(
            f"{self.__base_url}/api/collections/{collection_name}/records/{record_id}",
            json=api_params,
            headers=headers,
        ) as resp:
            return await resp.json()

    async def add_record(
        self, collection_name: str, client: aiohttp.ClientSession, **api_params
    ):
        headers = await self.__get_headers(client)
        async with client.post(
            f"{self.__base_url}/api/collections/{collection_name}/records",
            json=api_params,
            headers=headers,
        ) as resp:
            return await resp.json()

    async def delete_record(
        self,
        collection_name: str,
        record_id: str,
        client: aiohttp.ClientSession,
        **api_params,
    ):
        headers = await self.__get_headers(client)
        async with client.delete(
            f"{self.__base_url}/api/collections/{collection_name}/records/{record_id}",
            json=api_params,
            headers=headers,
        ) as resp:
            return await resp.json()
