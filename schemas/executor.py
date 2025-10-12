from typing import List

from pydantic import BaseModel

from database.tables import Availability
from schemas.profession import Job, Profession


class ExecutorAdd(BaseModel):
    tg_id: str
    name: str
    age: int
    description: int
    rate: str
    experience: str
    links: List[str]
    tags: List[str]
    availability: str = Availability.FREE
    contacts: str | None
    location: str | None
    langs: List[str]
    photo: bool
    profession: Profession
    jobs: List[Job]
    verified: bool = False