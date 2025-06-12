import os

from src.pocketbase import Pocketbase

POCKETBASE_URL = "http://188.120.232.32:8090"
PB = Pocketbase(POCKETBASE_URL)


class PocketbaseCollections:
    USERS = "users"
    ORGANIZATIONS = "organizations"
    TASKS = "tasks"
    GOALS = "goals"
    CHAT_MESSAGES = "chat_messages"
