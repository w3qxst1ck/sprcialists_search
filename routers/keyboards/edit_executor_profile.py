from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from schemas.executor import Executor
from settings import settings
from schemas.profession import Profession, Job


def profession_keyboard(professions: List[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура выбора профессии"""

    keyboard = InlineKeyboardBuilder()

    for p in professions:
        keyboard.row(InlineKeyboardButton(text=f"{p.title}", callback_data=f"choose_profession|{p.id}"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard


def jobs_keyboard(jobs: List[Job], selected_jobs: List[int]) -> InlineKeyboardBuilder:
    """Клавиатура выбора Jobs с мультиселектом"""
    keyboard = InlineKeyboardBuilder()

    for job in jobs:
        title = job.title

        # Помечаем выбранные работы
        if job.id in selected_jobs:
            title = "[ ✓ ] " + title

        keyboard.row(InlineKeyboardButton(text=f"{title}", callback_data=f"choose_jobs|{job.id}"))

    keyboard.adjust(1)

    # Подтвердить, если хотя бы одна Job выбрана
    if len(selected_jobs):
        keyboard.row(InlineKeyboardButton(text=f"{btn.CONTINUE}", callback_data="choose_jobs_done"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard


def send_to_verification_keyboard(tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения отправки анкеты на проверку после измененеия"""

    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отправить на проверку", callback_data=f"send_to_verification_confirmed|{tg_id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard


def to_profile_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура в меню исполнителя"""

    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.PROFILE}", callback_data=f"main_menu|executor_profile"))

    return keyboard


def continue_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Продолжить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="continue"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard


def skip_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Продолжить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Оставить пустым", callback_data="skip"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard


def cancel_edit_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены изменения параметров"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_edit_profile"))

    return keyboard