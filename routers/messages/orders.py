import datetime
from typing import List

from schemas.order import OrderAdd, Order
from utils.datetime_service import get_days_left_text


def get_order_card_message(order: OrderAdd) -> str:
    """Карточка заказа"""
    jobs = ", ".join([job.title for job in order.jobs])
    price = f"{order.price} ₽" if order.price else "жду предложений"

    # Склонение числа дни
    days_text = get_days_left_text(order.period)

    emoji = f"{order.profession.emoji} " if order.profession.emoji else ""

    msg = f"<b>{order.title}</b>\n\n" \
          f"{emoji}{order.profession.title} ({jobs})\n" \
          f"Описание задачи: <i>{order.task}</i>\n" \
          f"💵 Бюджет: {price}\n" \
          f"⏳ Срок: {order.period} {days_text}"

    # Прикрепленные файлы
    if order.files:
        filenames_text = ", ".join([file.filename for file in order.files])
        msg += f"\n📎 Файлы: {filenames_text}"

    # Особые требования
    if order.requirements:
        msg += f"\n⚠️ Требования: {order.requirements}"

    return msg


def get_my_orders_list(orders: List[Order]) -> str:
    """Список размещенных заказов"""
    msg = f"📋 <b>Размещенные заказы</b>\n\n"

    for idx, order in enumerate(orders, start=1):
        # Склонение числа дни
        days_text = get_days_left_text(order.period)

        # Бюджет
        price = f"{order.price} ₽" if order.price else "не указана"

        # Прикрепленные файлы
        if order.files:
            filenames = ", ".join([file.filename for file in order.files])
            filenames_text = f"| 📎 {filenames}"
        else:
            filenames_text = ""

        msg += f"<b>{idx}</b>. {order.title} \n" \
               f"🗓️ {order.period} {days_text} | 💵 {price} {filenames_text}\n\n"

    msg += "\nЧтобы перейти в заказ выберите соответствующий номер с помощью клавиатуры ниже"

    return msg