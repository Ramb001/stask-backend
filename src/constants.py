import os

from src.pocketbase import Pocketbase

POCKETBASE_URL = "http://127.0.0.1:8090"
PB = Pocketbase(POCKETBASE_URL)


class PocketbaseCollections:
    USERS = "users"
    ORGANIZATIONS = "organizations"
