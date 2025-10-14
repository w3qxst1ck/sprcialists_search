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


def all_reasons_keyboard(reasons: list[RejectReason], user_tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура со всем причинами отказа"""
    keyboard = InlineKeyboardBuilder()

    for reason in reasons:
        keyboard.row(
            InlineKeyboardButton(text=f"{reason.reason}", callback_data=f"reject_reason|{reason.id}|{user_tg_id}")
        )
    keyboard.adjust(1)
    return keyboard


def send_reject_to_user_keyboard(reason: RejectReason, user_tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура для отправки отказа пользователю"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text="Отправить отказ", callback_data=f"send_reject|{reason.id}|{user_tg_id}"))
    # keyboard.row(InlineKeyboardButton(text="<<Назад", callback_data=f"reject_reason|{reason.id}|{client_tg_id}"))
    keyboard.adjust(1)
    return keyboard