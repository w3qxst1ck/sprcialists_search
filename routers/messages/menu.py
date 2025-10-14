from database.tables import UserRoles


def get_menu_message(role: str) -> str:
    """Сообщения для главного меню"""
    if role == UserRoles.CLIENT.value:
        return "Главное меню (Ваш текс)"

