from typing import List

from pydantic import BaseModel


class Profession(BaseModel):
    id: int
    title: str
    tag: str


class Job(BaseModel):
    id: int
    title: str
    tag: str
    profession_id: int

