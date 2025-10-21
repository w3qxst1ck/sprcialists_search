from typing import List

from pydantic import BaseModel

from database.tables import Availability
from schemas.profession import Job, Profession


class ExecutorAdd(BaseModel):
    tg_id: str
    name: str
    age: int
    description: str
    rate: str
    experience: str
    links: List[str]
    availability: str = Availability.FREE
    contacts: str | None
    location: str | None
    photo: bool
    profession: Profession
    jobs: List[Job]
    verified: bool = False


class Executor(ExecutorAdd):
    id: int


class RejectReason(BaseModel):
    id: int
    reason: str
    text: str