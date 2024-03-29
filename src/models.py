from pydantic import BaseModel


class UpdateStatus(BaseModel):
    task_id: str
    status: str
    user_status: "Owner" or "Worker"
