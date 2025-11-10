from pydantic import BaseModel


class ClientAdd(BaseModel):
    tg_id: str
    name: str


class Client(ClientAdd):
    id: int


class RejectReason(BaseModel):
    id: int
    reason: str
    text: str
    period: int

