from schemas.order import Order
from utils.datetime_service import get_days_left_text


def response_on_order_message(cover_letter: str, order: Order, ex_tg_username: str, ex_name: str) -> str:
    """Сообщение для клиента при отклике исполнителя"""
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

    # Формируем краткое описание заказа
    msg = f"Новый отклик по твоему заказу!\n" \
          f"\n<b>{order.title}</b>\n" \
          f"🗓️ {order.period} {days_text} | 💵 {price} {filenames_text}\n\n"

    # Прикрепляем сопроводительный текст
    msg += f"<i>\"{cover_letter}\"</i>\n\n"

    # Добавляем ссылку на исполнителя
    msg += f"Обсуди детали в чате с исполнителем 👉 <a href='https://t.me/{ex_tg_username}'><u>{ex_name}</u></a>\n"
    return msg
