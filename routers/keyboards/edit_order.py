from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from schemas.executor import Executor
from settings import settings
from schemas.profession import Profession, Job


def profession_keyboard(professions: List[Profession], order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура выбора профессии"""

    keyboard = InlineKeyboardBuilder()

    for p in professions:
        keyboard.row(InlineKeyboardButton(text=f"{p.title}", callback_data=f"choose_profession|{p.id}"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"my_order|{order_id}"))

    return keyboard


def jobs_keyboard(jobs: List[Job], selected_jobs: List[int], order_id: int) -> InlineKeyboardBuilder:
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
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"my_order|{order_id}"))

    return keyboard


def to_orders_list_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура в список размещенных заказов"""

    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.MY_ORDERS}", callback_data=f"my_orders_list"))

    return keyboard


def to_order_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура к заказу"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data=f"my_order|{order_id}"))

    return keyboard


def cancel_skip_edit_order_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура отмены или пропуска изменения параметров"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Оставить пустым", callback_data=f"skip"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"my_order|{order_id}"))

    return keyboard


def continue_cancel_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура Продолжить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="continue"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"my_order|{order_id}"))

    return keyboard


def cancel_edit_order_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура отмены изменения параметров"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"my_order|{order_id}"))

    return keyboard
