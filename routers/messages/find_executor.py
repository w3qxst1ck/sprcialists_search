from schemas.executor import ExecutorShow
from routers.buttons import buttons as btn
from settings import settings
from utils.age import get_age_text


def contact_with_executor(executor: ExecutorShow) -> str:
    """Сообщение о связи с исполнителем"""
    msg = f"Вы можете перейти в чат с исполнителем <a href='tg://user?id={executor.tg_id}'>{executor.name}</a>\n"
    if executor.contacts:
          msg += f"Или связаться с ним при помощи указанных контактных данных {executor.contacts}\n\n"
    else:
        msg += "\n"

    msg += f"Вы также можете отправить ему заявку через бота по кнопке \"{btn.CONTACT_WITH}\""

    return msg
