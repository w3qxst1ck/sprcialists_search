from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from routers.buttons import menu as btn


def main_menu_keyboard(admin: bool) -> InlineKeyboardBuilder:
    """Клавиатура главного меню"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text=f"{btn.SETTINGS}", callback_data="menu|settings"),
        InlineKeyboardButton(text=f"{btn.CARDS}", callback_data="menu|cards"),
        InlineKeyboardButton(text=f"{btn.ORDERS}", callback_data="menu|orders"),
    )

    if admin:
        keyboard.row(InlineKeyboardButton(text=f"{btn.ADMIN}", callback_data="menu|admin"))

    return keyboard