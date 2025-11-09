from schemas.executor import ExecutorAdd, Executor
from settings import settings
from utils.age import get_age_text
from routers.buttons import buttons as btn


def get_executor_profile_message(executor: ExecutorAdd | Executor) -> str:
    """Анкета исполнителя для показа при регистрации"""
    age = get_age_text(executor.age)
    jobs = ", ".join([job.title for job in executor.jobs])
    links = "\n".join(executor.links)
    contacts = f"📞 {executor.contacts}\n" if executor.contacts else ""
    location = f"📍 {executor.location}\n" if executor.location else ""
    emoji = f"{executor.profession.emoji}" if executor.profession.emoji else ""

    msg = f"👤 {executor.name}, {age}\n" \
          f"{emoji} {executor.profession.title} ({jobs}). {executor.experience}\n" \
          f"💵 {executor.rate}\n" \
          f"{location}" \
          f"{contacts}" \
          f"📎 Портфолио:\n\n{links}\n\n" \
          f"О себе: {executor.description}"

    return msg


def executor_card_for_admin_verification(executor: ExecutorAdd) -> str:
    """Анкета исполнителя для верификации админами в группе"""
    msg = get_executor_profile_message(executor)

    verified = "✔️ Подтверждена" if executor.verified else "🚫 Не подтверждена"

    msg += f"\n\n{verified}"

    return msg


def edited_executor_card_for_admin_verification(executor: ExecutorAdd) -> str:
    """Измененная анкета исполнителя для верификации админами в группе"""
    msg = get_executor_profile_message(executor)

    verified = "✔️ Подтверждена" if executor.verified else "🚫 Не подтверждена"

    msg += f"\n\n{verified}"

    msg += "\n\n<i>*Исполнитель внес изменения в анкету и отправил на проверку</i>"

    return msg


def executor_profile_to_show(executor: Executor, in_favorites: bool = False) -> str:
    """Карточка исполнителя для показа в ленте"""
    msg = get_executor_profile_message(executor)

    if in_favorites:
        msg = "<i>⭐ В избранном</i>\n\n" + msg

    return msg


def instruction_message() -> str:
    """Сообщение с инструкцией для исполнителей"""
    msg = f"<b>🔍 Как пользоваться ботом:</b>\n\n" \
          f" В главном меню ты найдешь 4 раздела:\n\n" \
          f"<b>{btn.FIND_ORDERS}</b>\n" \
          f"Выбери нужное направление — и бот покажет актуальные заказы от клиентов по твоему запросу.\n\n" \
          f"<b>{btn.PROFILE}</b>\n" \
          f"Здесь ты можешь посмотреть, как выглядит твоя анкета и при желании изменить ее.\n\n" \
          f"<b>{btn.FAVORITE}</b>\n" \
          f"Добавляй понравившиеся заказы в избранное, чтобы не потерять. Возвращайся к ним в любое время через этот раздел.\n\n" \
          f"<b>{btn.STATUS}</b>\n" \
          f"Ты можешь приостановить показ своей анкеты в боте, если не хочешь принимать новые заказы. В любой момент ты снова сможешь сделать анкету активной через этот раздел."

    return msg
