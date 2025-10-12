from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType


def pick_client_type_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура для выбора типа клиента"""
    keyboard = InlineKeyboardBuilder()

    for client_type in ClientType:
        keyboard.row(InlineKeyboardButton(text=f"{client_type.value.capitalize()}", callback_data=f"client_type|{client_type.name}"))
        print(client_type)

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def skip_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Пропустить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Пропустить", callback_data="skip"))
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard
