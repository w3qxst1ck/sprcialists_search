from schemas.client import ClientAdd
from settings import settings
from routers.buttons import buttons as btn


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


def instruction_msg() -> str:
    """Сообщение с инструкцией для клиента"""
    msg = f"<b>Как пользоваться ботом</b>\n\n" \
          f"В главном меню ты найдешь 3 раздела:\n\n" \
          f"<b>{btn.FIND_EX}</b>\n" \
          f"Выбери нужное направление — и бот покажет анкеты проверенных исполнителей по твоему запросу.\n\n" \
          f"<b>{btn.MY_ORDERS}</b>\n" \
          f"Здесь ты можешь разместить свой заказ — он будет показан подходящим исполнителям. Жди откликов и выбирай, с кем начать работу.\n\n" \
          f"<b>{btn.FAVORITE}</b>\n" \
          f"Добавляй понравившиеся анкеты в избранное, чтобы не потерять. Возвращайся к ним в любое время через этот раздел."
    return msg

