import datetime
from typing import List

from pydantic import BaseModel

from database.tables import UserRoles


class UserAdd(BaseModel):
    tg_id: str
    username: str | None
    firstname: str | None
    lastname: str | None
    role: str | None = None


class User(UserAdd):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    is_admin: bool
    is_banned: bool




