from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class UpdateStatus(BaseModel):
    task_id: str
    status: str
    user_status: str


class DeleteWorker(BaseModel):
    organization_id: str
    worker_id: str


class UpdateUserInfo(BaseModel):
    user_id: str
    new_name: str


class DeleteOrganization(BaseModel):
    organization_id: str


class LeaveOrganization(BaseModel):
    organization_id: str
    user_id: str


class Goal(BaseModel):
    user_id: str
    message: str
    organization_id: str
    department: str


class Task(BaseModel):
    id: Optional[str]
    title: str
    description: str
    status: str = "pending"
    created_at: datetime = datetime.now()
    goal_id: str
    deadline: str
    recommended_executors: int
    priority: str
    depends_on: List[str] = []
    workers: Optional[List[str]] = []


class TaskDecomposition(BaseModel):
    goal_id: str
    tasks: List[Task]


class TaskApproval(BaseModel):
    user_id: str
    goal_id: str
    organization_id: str
    tasks: List[Task]


class ChatMessage(BaseModel):
    id: Optional[str]
    chat_id: str
    user_id: Optional[str]  # None если это AI
    role: str  # "user" или "ai"
    content: str
    timestamp: datetime = datetime.now()
    goal_id: Optional[str] = None
