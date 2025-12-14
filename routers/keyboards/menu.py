from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.tables import ClientType, UserRoles
from routers.buttons import buttons as btn
from routers.buttons import buttons
from settings import settings


def main_menu(user_role: str, is_admin: bool = False) -> InlineKeyboardBuilder:
    """Клавиатура с главным меню"""
    keyboard = InlineKeyboardBuilder()

    # Меню для клиента
    if user_role == UserRoles.CLIENT.value:
        keyboard.row(InlineKeyboardButton(text=f"{btn.FIND_EX}", callback_data=f"main_menu|find_executor"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.MY_ORDERS}", callback_data=f"main_menu|my_orders"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.FAVORITE}", callback_data=f"main_menu|client_favorites"))

        keyboard.adjust(2)

    # Меню для исполнителя
    elif user_role == UserRoles.EXECUTOR.value:
        keyboard.row(InlineKeyboardButton(text=f"{btn.FIND_ORDERS}", callback_data=f"main_menu|find_order"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.PROFILE}", callback_data=f"main_menu|executor_profile"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.FAVORITE}", callback_data=f"main_menu|executor_favorites"))
        keyboard.row(InlineKeyboardButton(text=f"{btn.STATUS}", callback_data=f"main_menu|change_ex_status"))


        keyboard.adjust(2)

    # if is_admin:
    #     keyboard.row(InlineKeyboardButton(text=f"{btn.ADMIN}", callback_data=f"main_menu|admin_menu"))

    return keyboard