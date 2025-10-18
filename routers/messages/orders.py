from typing import List

from schemas.order import OrderAdd, Order
from utils.datetime_service import convert_date_time_to_str


def get_order_card_message(order: OrderAdd) -> str:
    """Карточка заказа"""
    jobs = ", ".join([job.title for job in order.jobs])
    price = order.price if order.price else "жду предложений"
    deadline = convert_date_time_to_str(order.deadline)

    msg = f"<b>{order.title}</b>\n\n" \
          f"{order.profession.title} ({jobs})\n" \
          f"Описание задачи: <i>{order.task}</i>\n" \
          f"💵 Бюджет: {price}\n" \
          f"⏳ Срок: {deadline}"

    if order.requirements:
        msg += f"\n⚠️ Требования: {order.requirements}"

    return msg


def get_my_orders_list(orders: List[Order]) -> str:
    """Список размещенных заказов"""
    msg = f"📋 <b>Размещенные заказы</b>\n\n"

    for idx, order in enumerate(orders, start=1):
        deadline_str = convert_date_time_to_str(order.deadline)
        msg += f"<b>{idx}</b>. {order.title} | Срок: {deadline_str}\n"

    msg += "\nЧтобы перейти в заказ выберите соответствующий номер с помощью клавиатуры ниже"

    return msg