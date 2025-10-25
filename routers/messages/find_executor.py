import urllib.parse

from schemas.client import Client
from schemas.executor import Executor


def contact_with_executor(executor: Executor, username: str | None) -> str:
    """Сообщение о связи с исполнителем"""
    # Если у исполнителя не указан username для формирования ссылки
    if not username:
        return f"В настоящий момент невозможно связаться с исполнителем <i>{executor.name}</i>"

    start_dialog_text = "Привет! Я с HireBot ✨\n"
    encoded_text = urllib.parse.quote(start_dialog_text)

    msg = f"Обсудите детали заказа в чате с исполнителем!\n" \
          f"👉 <a href='https://t.me/{username}?text={encoded_text}'><u>{executor.name}</u></a>\n"

    if executor.contacts:
          msg += f"Или свяжитесь с ним при помощи указанных контактных данных {executor.contacts}\n\n"
    else:
        msg += "\n"

    return msg


def contact_with_client(client_tg_username: str | None, client: Client) -> str:
    """Формируем сообщение для связи с заказчиком"""
    if not client_tg_username:
        return f"В настоящий момент невозможно связаться с заказчиком <i>{client.name}</i>"

    start_dialog_text = "Привет! Я с HireBot ✨\n"
    encoded_text = urllib.parse.quote(start_dialog_text)

    msg = f"Обсудите детали заказа в чате с заказчиком!\n" \
          f"👉 <a href='https://t.me/{client_tg_username}?text={encoded_text}'><u>{client.name}</u></a>\n"

    return msg
