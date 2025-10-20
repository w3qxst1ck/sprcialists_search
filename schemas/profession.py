from typing import List

from pydantic import BaseModel


class Profession(BaseModel):
    id: int
    title: str


class Job(BaseModel):
    id: int
    title: str
    profession_id: int

