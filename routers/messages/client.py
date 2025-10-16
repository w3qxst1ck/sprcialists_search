from schemas.client import ClientAdd
from settings import settings


def get_client_profile_message(client: ClientAdd) -> str:
    """Анкета исполнителя для показа при регистрации"""
    if client.langs:
        langs = "/".join([settings.languages[lang] for lang in client.langs])
    else:
        langs = ""

    if client.links:
        links = "📎 "
        links += " | ".join(client.links)
        links += "\n"
    else:
        links = ""

    contacts = client.contacts if client.contacts else "не указаны"
    location = client.location if client.location else "не указан"
    # verified = "✔️ Подтверждена" if client.verified else "🚫 Не подтверждена"

    msg = f"👤 {client.name} ({client.type.value.capitalize()}) {langs}\n" \
          f"{links}" \
          f"О себе: {client.description if client.description else 'не указано'}\n" \
          f"Город: {location}\n" \
          f"Контакты: {contacts}" \
          # f"Верификация: {verified}"

    return msg