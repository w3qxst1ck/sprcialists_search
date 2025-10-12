from typing import List

from schemas.profession import Profession, Job
from settings import settings
from utils.age import get_age_text


def get_executor_profile_message(data: dict, profession: Profession, jobs: List[Job]) -> str:
    """Анкета исполнителя для показа при регистрации"""
    age = get_age_text(data["age"])
    jobs = ", ".join([job.title for job in jobs])
    langs = "/".join([settings.languages[lang] for lang in data["selected_langs"]])
    tags = " ".join([f"#{tag}" for tag in data["tags"]])
    links = " | ".join(data["links"])
    contacts = data["contacts"] if data["contacts"] else "не указаны"
    location = data["location"] if data["location"] else "не указан"

    msg = f"👤 {data['name']}, {age} — {profession.title} ({jobs})\n" \
          f"💼 {data['experience']} | 💲 {data['rate']} | {langs}\n" \
          f"🏷️ {tags}\n" \
          f"📎 {links}\n" \
          f"О себе: {data['description']}\n" \
          f"Город: {location}\n" \
          f"Контакты: {contacts}"

    return msg