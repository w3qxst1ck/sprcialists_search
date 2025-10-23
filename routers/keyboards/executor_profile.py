from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from settings import settings
from schemas.profession import Profession, Job


def executor_profile_keyboard(cv_exists: bool = False) -> InlineKeyboardBuilder:
    """Клавиатура меню исполнителя"""

    keyboard = InlineKeyboardBuilder()

    if cv_exists:
        keyboard.row(InlineKeyboardButton(text=f"📎 Скачать резюме", callback_data=f"download_cv"))
        keyboard.row(InlineKeyboardButton(text=f"🗑️ Удалить резюме", callback_data=f"delete_cv"))
    else:
        keyboard.row(InlineKeyboardButton(text=f"📝 Загрузить резюме", callback_data=f"upload_cv"))

    # Кнопка назад
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))

    return keyboard


def to_executor_profile_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура в меню исполнителя"""

    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.PROFILE}", callback_data=f"main_menu|executor_profile"))

    return keyboard


def back_from_cv_file_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура в меню исполнителя"""

    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data=f"main_menu|executor_profile"))

    return keyboard


def cancel_upload_cv_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены загрузки резюме"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_upload_cv"))

    return keyboard