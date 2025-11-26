import datetime

from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: int
    executor_id: int
    created_at: datetime.datetime
    text: str
