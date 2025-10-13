from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType, UserRoles
from routers.buttons import menu
from settings import settings


def main_menu(user_role: str) -> InlineKeyboardBuilder:
    """Клавиатура с главным меню"""
    keyboard = InlineKeyboardBuilder()

    # Меню для клиента
    if user_role == UserRoles.CLIENT.value:
        keyboard.row(InlineKeyboardButton(text="🔍Найти исполнителя", callback_data=f"main_menu|find_executor"))
        keyboard.row(InlineKeyboardButton(text="📋 Мои заказы", callback_data=f"main_menu|my_orders"))
        keyboard.row(InlineKeyboardButton(text="👤 Профиль", callback_data=f"main_menu|my_profile"))
        keyboard.row(InlineKeyboardButton(text=f"{menu.SETTINGS}", callback_data=f"main_menu|client_settings"))

        keyboard.adjust(2)

    # Меню для исполнителя
    else:
        pass

    return keyboard