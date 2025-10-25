from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from database.tables import ClientType
from schemas.executor import Executor
from schemas.order import Order
from settings import settings


def favorites_executor_keyboard(executors: list[Executor], current_index: int) -> InlineKeyboardBuilder:
    """Клавиатура для вывода избранных исполнителей"""
    keyboard = InlineKeyboardBuilder()

    # Получаем текущего исполнителя
    executor = executors[current_index]

    keyboard.row(
        InlineKeyboardButton(text="<", callback_data="prev_ex"),
        InlineKeyboardButton(text=f"{current_index + 1}/{len(executors)}", callback_data="None"),
        InlineKeyboardButton(text=">", callback_data=f"next_ex")
    )

    keyboard.row()
    keyboard.adjust(3)

    # Добавляем кнопку назад
    keyboard.row(InlineKeyboardButton(text=f"Удалить ⭐", callback_data=f"delete_fav|{executor.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="back_from_favorites_feed"))

    return keyboard


def back_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура назад"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))
    return keyboard


def favorites_orders_keyboard(orders: list[Order], current_index: int) -> InlineKeyboardBuilder:
    """Клавиатура для вывода избранных заказов"""
    keyboard = InlineKeyboardBuilder()

    # Получаем текущего исполнителя
    order = orders[current_index]

    keyboard.row(
        InlineKeyboardButton(text="<", callback_data="prev"),
        InlineKeyboardButton(text=f"{current_index + 1}/{len(orders)}", callback_data="None"),
        InlineKeyboardButton(text=">", callback_data=f"next")
    )

    keyboard.row()
    keyboard.adjust(3)

    # Добавляем кнопку назад
    keyboard.row(InlineKeyboardButton(text=f"Удалить ⭐", callback_data=f"delete_fav_order|{order.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))

    return keyboard