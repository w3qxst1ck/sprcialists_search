from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from routers.buttons import buttons as btn

from schemas.profession import Profession


def profession_keyboard(professions: List[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура с выбором профессии для создания заказа"""
    keyboard = InlineKeyboardBuilder()

    for profession in professions:
        keyboard.row(InlineKeyboardButton(text=f"{profession.title}", callback_data=f"choose_profession|{profession.id}"))

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_create_order"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_create_order"))

    return keyboard