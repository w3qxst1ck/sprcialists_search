from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def confirm_registration_executor_keyboard(tg_id: str, executor_id: int) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения регистрации"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"executor_confirm|{tg_id}|{executor_id}"),
        InlineKeyboardButton(text="Отклонить ❌", callback_data=f"executor_cancel|{tg_id}|{executor_id}")
    )

    return keyboard