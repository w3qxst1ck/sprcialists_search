from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from settings import settings
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
            title = "[ ✓ ] " + title

        keyboard.row(InlineKeyboardButton(text=f"{title}", callback_data=f"choose_jobs|{job.id}"))

    keyboard.adjust(2)

    # Подтвердить, если хотя бы одна Job выбрана
    if len(selected_jobs):
        keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="choose_jobs_done"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def choose_langs_keyboard(selected_langs: List[str]) -> InlineKeyboardBuilder:
    """Клавиатура мультиселекта языков"""
    keyboard = InlineKeyboardBuilder()

    for lang, flag in settings.languages.items():
        title = flag

        # Помечаем выбранные языки
        if lang in selected_langs:
            title = "[ ✓ ] " + flag

        keyboard.row(InlineKeyboardButton(text=f"{title}", callback_data=f"choose_langs|{lang}"))

    keyboard.adjust(3)

    # Подтвердить, если хотя бы один язык выбран
    if len(selected_langs):
        keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="choose_langs_done"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def confirm_registration_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура подтверждения регистрации"""
    keyboard = InlineKeyboardBuilder()

    # Кнопка подтвердить
    keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="confirm_registration"))
    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def continue_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Продолжить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="continue"))
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