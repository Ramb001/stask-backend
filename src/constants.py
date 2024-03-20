import os

from src.pocketbase import Pocketbase

POCKETBASE_URL = "http://45.143.94.202:8090"
PB = Pocketbase(POCKETBASE_URL)


class PocketbaseCollections:
    USERS = "users"
    ORGANIZATIONS = "organizations"
