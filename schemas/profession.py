from typing import List

from pydantic import BaseModel


class ProfessionAdd(BaseModel):
    title: str
    emoji: str | None = None


class Profession(ProfessionAdd):
    id: int


class Job(BaseModel):
    id: int
    title: str
    profession_id: int

