from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from schemas.client import RejectReason
from routers.buttons import buttons as btn
from schemas.profession import Profession


def confirm_registration_executor_keyboard(tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения регистрации исполнителя"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"executor_confirm|{tg_id}"),
        InlineKeyboardButton(text="Отклонить ❌", callback_data=f"executor_cancel|{tg_id}")
    )

    return keyboard


def confirm_edit_executor_keyboard(tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения изменения анкеты исполнителя"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"executor_edit_confirm|{tg_id}"),
        InlineKeyboardButton(text="Отклонить ❌", callback_data=f"executor_edit_cancel|{tg_id}")
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


def admin_menu_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура меню админа"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"💼 Добавить профессию", callback_data=f"add_profession"))
    keyboard.row(InlineKeyboardButton(text=f"🛠️ Добавить раздел профессии", callback_data=f"add_job"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data=f"main_menu"))

    return keyboard


def profession_keyboard(professions: List[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура выбора профессии"""

    keyboard = InlineKeyboardBuilder()

    for p in professions:
        keyboard.row(InlineKeyboardButton(text=f"{p.title}", callback_data=f"choose_profession|{p.id}"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"admin_cancel"))

    return keyboard


def back_to_main_menu_keyboard() -> InlineKeyboardBuilder:
    """В главное меню"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data=f"main_menu"))

    return keyboard


def yes_no_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура ДА/НЕТ"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text=f"Да", callback_data=f"confirm"),
        InlineKeyboardButton(text=f"Нет", callback_data=f"admin_cancel")
    )

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Кнопка отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data=f"admin_cancel"))

    return keyboard