from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import Availability
from routers.buttons import buttons as btn
from schemas.executor import Executor
from settings import settings
from schemas.profession import Profession, Job


def executor_profile_keyboard(cv_exists: bool = False) -> InlineKeyboardBuilder:
    """Клавиатура меню исполнителя"""

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text=f"{btn.ONE}", callback_data=f"edit_executor|photo"),
        InlineKeyboardButton(text=f"{btn.TWO}", callback_data=f"edit_executor|profession"),
        InlineKeyboardButton(text=f"{btn.THREE}", callback_data=f"edit_executor|rate"),
        InlineKeyboardButton(text=f"{btn.FOUR}", callback_data=f"edit_executor|experience"),
        InlineKeyboardButton(text=f"{btn.FIVE}", callback_data=f"edit_executor|description"),
        InlineKeyboardButton(text=f"{btn.SIX}", callback_data=f"edit_executor|contacts"),
        InlineKeyboardButton(text=f"{btn.SEVEN}", callback_data=f"edit_executor|location"),
        InlineKeyboardButton(text=f"{btn.EIGHT}", callback_data=f"edit_executor|links"),
    )
    keyboard.adjust(4)

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


def executor_change_status_keyboard(executor: Executor) -> InlineKeyboardBuilder:
    """Клавиатура для изменения статуса исполнителя"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(
        text=f"{'[ ✓ ] ' if executor.availability == Availability.FREE.value else ''}Принимаю заказы",
                                      callback_data="set_status|free"))
    keyboard.row(InlineKeyboardButton(
        text=f"{'[ ✓ ] ' if executor.availability == Availability.BUSY.value else ''}Недоступен",
        callback_data="set_status|busy"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data=f"main_menu"))

    return keyboard

