import datetime

from pydantic import BaseModel


class BlockedUserAdd(BaseModel):
    user_tg_id: str
    expire_date: datetime.datetime
    user_id: int


class BlockedUser(BlockedUserAdd):
    id: int
