from schemas.executor import ExecutorAdd, Executor
from settings import settings
from utils.age import get_age_text


def get_executor_profile_message(executor: ExecutorAdd | Executor) -> str:
    """Анкета исполнителя для показа при регистрации"""
    age = get_age_text(executor.age)
    jobs = ", ".join([job.title for job in executor.jobs])
    # langs = "/".join([settings.languages[lang] for lang in executor.langs])
    # tags = " ".join([f"#{tag}" for tag in executor.tags])
    links = "\n".join(executor.links)
    # contacts = executor.contacts if executor.contacts else "не указаны"
    location = f"📍 {executor.location}\n" if executor.location else ""
    verified = "✔️ Подтверждена" if executor.verified else "🚫 Не подтверждена"

    msg = f"👤 {executor.name}, {age}\n" \
          f"🎨 {executor.profession.title} ({jobs}). {executor.experience}\n" \
          f"💵 {executor.rate}\n" \
          f"{location}\n" \
          f"📎 Портфолио:\n\n{links}\n\n" \
          f"О себе: {executor.description}\n\n" \
          f"Верификация: {verified}"

    return msg


def executor_profile_to_show(executor: Executor, in_favorites: bool = False) -> str:
    """Карточка исполнителя для показа в ленте"""
    msg = get_executor_profile_message(executor)

    if in_favorites:
        msg = "<i>⭐ В избранном</i>\n\n" + msg

    return msg
