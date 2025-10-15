from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from schemas.client import RejectReason


def confirm_registration_executor_keyboard(tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения регистрации исполнителя"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"executor_confirm|{tg_id}"),
        InlineKeyboardButton(text="Отклонить ❌", callback_data=f"executor_cancel|{tg_id}")
    )

    return keyboard


def confirm_registration_client_keyboard(tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения регистрации клиента"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"client_confirm|{tg_id}"),
        InlineKeyboardButton(text="Отклонить ❌", callback_data=f"client_cancel|{tg_id}")
    )

    return keyboard


def select_reasons_keyboard(reasons: list[RejectReason], selected_reasons: List[int]) -> InlineKeyboardBuilder:
    """Клавиатура с мультивыбором причин отказа"""
    keyboard = InlineKeyboardBuilder()

    for reason in reasons:
        if reason.id in selected_reasons:
            text = f"[ ✓ ] {reason.reason}"
        else:
            text = reason.reason

        keyboard.row(InlineKeyboardButton(text=text, callback_data=f"reject_reason|{reason.id}"))

    # Кнопка Подтвердить
    if selected_reasons:
        keyboard.row(InlineKeyboardButton(text="Подтвердить", callback_data=f"reject_reasons_done"))

    return keyboard
