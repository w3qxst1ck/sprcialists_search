from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from database.tables import ClientType
from schemas.executor import Executor
from settings import settings


def favorites_executor_keyboard(executors: list[Executor], current_index: int) -> InlineKeyboardBuilder:
    """Клавиатура для вывода избранных исполнителей"""
    keyboard = InlineKeyboardBuilder()

    # Получаем текущего исполнителя
    executor = executors[current_index]

    # Устанавливаем условия для отображения кнопок
    can_go_left = current_index > 0
    can_go_right = current_index < len(executors) - 1

    # Формируем кнопки вправо и влево
    text = f"{btn.LEFT if can_go_left else btn.DISABLED}"
    left_button = InlineKeyboardButton(
        text=text,
        callback_data=f"{'prev_ex' if can_go_left else None}"
    )
    text = f"{btn.RIGHT if can_go_right else btn.DISABLED}"
    right_button = InlineKeyboardButton(
        text=text,
        callback_data=f"{'next_ex' if can_go_right else None}"
    )

    keyboard.row(left_button)
    keyboard.row(InlineKeyboardButton(text=f"Удалить ⭐", callback_data=f"delete_fav|{executor.id}"))
    keyboard.row(right_button)
    keyboard.adjust(3)

    # Добавляем кнопку назад
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="back_from_favorites_feed"))

    return keyboard


def back_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура назад"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))
    return keyboard
