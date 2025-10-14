from typing import List

from pydantic import BaseModel

from database.tables import ClientType


class ClientAdd(BaseModel):
    tg_id: str
    name: str
    type: ClientType
    description: str | None
    photo: bool

    # Optional
    verified: bool = False
    links: List[str] | None = None
    contacts: str | None = None
    location: str | None = None
    langs: List[str] | None = None


class RejectReason(BaseModel):
    id: int
    reason: str
    text: str

