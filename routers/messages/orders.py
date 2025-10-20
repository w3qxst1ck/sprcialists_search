import datetime
from typing import List

from schemas.order import OrderAdd, Order
from utils.datetime_service import convert_date_time_to_str, get_days_left_text


def get_order_card_message(order: OrderAdd) -> str:
    """Карточка заказа"""
    jobs = ", ".join([job.title for job in order.jobs])
    price = f"{order.price} ₽" if order.price else "жду предложений"

    # Количество дней цифрой
    days_left = order.deadline.day - datetime.datetime.now().day
    # Склонение числа дни
    days_str = get_days_left_text(days_left)

    msg = f"<b>{order.title}</b>\n\n" \
          f"{order.profession.title} ({jobs})\n" \
          f"Описание задачи: <i>{order.task}</i>\n" \
          f"💵 Бюджет: {price}\n" \
          f"⏳ Срок: {days_left} {days_str}"

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
        # Количество дней цифрой
        days_left = order.deadline.day - datetime.datetime.now().day
        # Склонение числа дни
        days_str = get_days_left_text(days_left)

        # Бюджет
        price = f"{order.price} ₽" if order.price else "не указана"

        # Прикрепленные файлы
        if order.files:
            filenames = ", ".join([file.filename for file in order.files])
            filenames_text = f"| 📎 {filenames}"
        else:
            filenames_text = ""

        msg += f"<b>{idx}</b>. {order.title} \n" \
               f"⏳ {days_left} {days_str} | 💵 {price} {filenames_text}\n\n"

    msg += "\nЧтобы перейти в заказ выберите соответствующий номер с помощью клавиатуры ниже"

    return msg