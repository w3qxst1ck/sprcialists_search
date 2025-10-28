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
    keyboard.row(InlineKeyboardButton(text=f"{btn.WRITE}", callback_data=f"write_fav_ex|{executor.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.DEL_FAV}", callback_data=f"delete_fav|{executor.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="back_from_favorites_feed"))

    return keyboard


def back_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура назад"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))
    return keyboard


def back_to_feed_keyboard() -> InlineKeyboardBuilder:
    """Назад в ленту избранных"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="back_to_fav_feed"))

    return keyboard


def favorites_orders_keyboard(orders: list[Order], current_index: int) -> InlineKeyboardBuilder:
    """Клавиатура для вывода избранных заказов"""
    keyboard = InlineKeyboardBuilder()

    # Получаем текущий заказ
    order = orders[current_index]

    keyboard.row(
        InlineKeyboardButton(text="<", callback_data="prev"),
        InlineKeyboardButton(text=f"{current_index + 1}/{len(orders)}", callback_data="None"),
        InlineKeyboardButton(text=">", callback_data=f"next")
    )

    keyboard.row()
    keyboard.adjust(3)

    # Кнопка скачать файлы, если они есть
    if order.files:
        keyboard.row(InlineKeyboardButton(text=f"📎 Скачать файлы", callback_data=f"files_for_order|{order.id}"))

    # Добавляем кнопку назад
    keyboard.row(InlineKeyboardButton(text=f"{btn.RESPOND}", callback_data=f"write_fav_order|{order.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.DEL_FAV}", callback_data=f"delete_fav_order|{order.id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))

    return keyboard


def confirm_send_cover_letter() -> InlineKeyboardBuilder:
    """Клавиатура для подтверждения отправки сопроводительного письма"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.SEND_COVER_LETTER}", callback_data="send_cover_letter"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="back_to_fav_feed"))
    return keyboard