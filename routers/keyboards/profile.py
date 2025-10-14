from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType
from routers.buttons import menu as btn
from settings import settings


def profile_menu() -> InlineKeyboardBuilder:
    """Клавиатура во вкладке профиль"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Изменить профиль",
                                      callback_data=f"client_profile|change_profile"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_client_registration"))

    return keyboard
