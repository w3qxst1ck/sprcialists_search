from schemas.executor import ExecutorAdd, Executor
from settings import settings
from utils.age import get_age_text


def get_executor_profile_message(executor: ExecutorAdd | Executor) -> str:
    """Анкета исполнителя для показа при регистрации"""
    age = get_age_text(executor.age)
    jobs = ", ".join([job.title for job in executor.jobs])
    links = "\n".join(executor.links)
    contacts = f"📞 {executor.contacts}\n" if executor.contacts else ""
    location = f"📍 {executor.location}\n" if executor.location else ""
    emoji = f"{executor.profession.emoji}" if executor.profession.emoji else ""

    # Поле верификация только по необходимости

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


def executor_profile_to_show(executor: Executor, in_favorites: bool = False) -> str:
    """Карточка исполнителя для показа в ленте"""
    msg = get_executor_profile_message(executor)

    if in_favorites:
        msg = "<i>⭐ В избранном</i>\n\n" + msg

    return msg
