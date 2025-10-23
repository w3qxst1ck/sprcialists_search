import urllib.parse

from schemas.executor import Executor
from routers.buttons import buttons as btn
from settings import settings
from utils.age import get_age_text


def contact_with_executor(executor: Executor) -> str:
    """Сообщение о связи с исполнителем"""
    start_dialog_text = "Привет! Я с HireBot ✨\n"
    encoded_text = urllib.parse.quote(start_dialog_text)

    msg = f"Обсудите детали заказа в чате с исполнителем!\n" \
          f"👉 <a href='https://t.me/aleksandr_andreew?text={encoded_text}'><u>{executor.name}</u></a>\n"

    if executor.contacts:
          msg += f"Или свяжитесь с ним при помощи указанных контактных данных {executor.contacts}\n\n"
    else:
        msg += "\n"

    return msg
