from datetime import datetime
from typing import List

from pydantic import BaseModel

from schemas.profession import Job, Profession


class OrderAdd(BaseModel):
    client_id: int
    tg_id: str
    profession: Profession
    jobs: List[Job]
    title: str
    task: str
    price: str | None
    deadline: datetime
    requirements: str | None
    created_at: datetime
    is_active: bool
    files: List["TaskFileAdd"] | List["TaskFile"] = []


class Order(OrderAdd):
    id: int


class TaskFileAdd(BaseModel):
    file_id: str
    filename: str


class TaskFile(TaskFileAdd):
    id: int
    order_id: int
