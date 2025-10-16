from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType, UserRoles
from routers.buttons import buttons as btn
from routers.buttons import buttons
from settings import settings


def main_menu(user_role: str) -> InlineKeyboardBuilder:
    """Клавиатура с главным меню"""
    keyboard = InlineKeyboardBuilder()

    # Меню для клиента
    if user_role == UserRoles.CLIENT.value:
        keyboard.row(InlineKeyboardButton(text=f"{btn.FIND_EX}", callback_data=f"main_menu|find_executor"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.MY_ORDERS}", callback_data=f"main_menu|my_orders"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.PROFILE}", callback_data=f"main_menu|my_profile"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.FAVORITE}", callback_data=f"main_menu|client_favorites"))

        keyboard.adjust(2)

    # Меню для исполнителя
    elif user_role == UserRoles.EXECUTOR.value:
        keyboard.row(InlineKeyboardButton(text=f"{btn.FIND_ORDERS}", callback_data=f"main_menu|find_order"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.PROFILE}", callback_data=f"main_menu|executor_profile"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.FAVORITE}", callback_data=f"main_menu|favorite_orders"))

        keyboard.adjust(2)

    return keyboard