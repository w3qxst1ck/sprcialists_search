from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType
from settings import settings


def pick_client_type_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура для выбора типа клиента"""
    keyboard = InlineKeyboardBuilder()

    for client_type in ClientType:
        keyboard.row(InlineKeyboardButton(text=f"{client_type.value.capitalize()}",
                                          callback_data=f"client_type|{client_type.value}"))

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_executor_registration"))

    return keyboard


def choose_langs_keyboard(selected_langs: list[str]) -> InlineKeyboardBuilder:
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
    keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="confirm_client_registration"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_verification_client"))

    return keyboard


def skip_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Пропустить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Пропустить", callback_data="skip"))
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_client_registration"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="cancel_client_registration"))

    return keyboard
