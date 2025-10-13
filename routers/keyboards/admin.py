from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


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