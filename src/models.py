from pydantic import BaseModel


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
