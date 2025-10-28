from typing import List

from pydantic import BaseModel


class ProfessionAdd(BaseModel):
    title: str
    emoji: str | None = None


class Profession(ProfessionAdd):
    id: int


class JobAdd(BaseModel):
    title: str
    profession_id: int


class Job(JobAdd):
    id: int


