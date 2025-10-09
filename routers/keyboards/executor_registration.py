from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from schemas.profession import Profession, Job


def profession_keyboard(professions: List[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура выбора профессии"""

    keyboard = InlineKeyboardBuilder()

    for p in professions:
        keyboard.row(InlineKeyboardButton(text=f"{p.title}", callback_data=f"choose_profession|{p.id}"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def jobs_keyboard(jobs: List[Job], selected_jobs: List[int]) -> InlineKeyboardBuilder:
    """Клавиатура выбора Jobs с мультиселектом"""

    keyboard = InlineKeyboardBuilder()

    for job in jobs:
        title = job.title

        # Помечаем выбранные работы
        if job.id in selected_jobs:
            title = "[ ✓ ]" + title

        keyboard.row(InlineKeyboardButton(text=f"{title}", callback_data=f"choose_jobs|{job.id}"))

    # Подтвердить, если хотя бы одна Job выбрана
    if len(selected_jobs):
        keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="choose_jobs_done"))

    keyboard.adjust(2)

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard