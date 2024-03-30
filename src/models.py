from pydantic import BaseModel


class UpdateStatus(BaseModel):
    task_id: str
    status: str
    user_status: str


class DeleteWorker(BaseModel):
    organization_id: str
    worker_id: str
