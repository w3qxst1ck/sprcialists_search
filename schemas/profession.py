from typing import List

from pydantic import BaseModel


class Profession(BaseModel):
    id: int
    title: str
    emoji: str | None = None


class Job(BaseModel):
    id: int
    title: str
    profession_id: int

