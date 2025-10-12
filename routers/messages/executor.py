from schemas.executor import ExecutorAdd
from settings import settings
from utils.age import get_age_text


def get_executor_profile_message(executor: ExecutorAdd) -> str:
    """Анкета исполнителя для показа при регистрации"""
    age = get_age_text(executor.age)
    jobs = ", ".join([job.title for job in executor.jobs])
    langs = "/".join([settings.languages[lang] for lang in executor.langs])
    tags = " ".join([f"#{tag}" for tag in executor.tags])
    links = " | ".join(executor.links)
    contacts = executor.contacts if executor.contacts else "не указаны"
    location = executor.location if executor.location else "не указан"
    verified = "✔️ Подтверждена" if executor.verified else "🚫 Не подтверждена"

    msg = f"👤 {executor.name}, {age} — {executor.profession.title} ({jobs})\n" \
          f"💼 {executor.experience} | 💲 {executor.rate} | {langs}\n" \
          f"🏷️ {tags}\n" \
          f"📎 {links}\n" \
          f"О себе: {executor.description}\n" \
          f"Город: {location}\n" \
          f"Контакты: {contacts}\n" \
          f"Верификация: {verified}"

    return msg