from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from routers.buttons import buttons as btn
from database.tables import ClientType
from schemas.profession import Profession, Job
from settings import settings


def professions_keyboard(professions: list[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура для выбора профессии"""
    keyboard = InlineKeyboardBuilder()

    for prof in professions:
        keyboard.row(InlineKeyboardButton(
            text=f"{prof.title}",
            callback_data=f"find_ex_prof|{prof.id}")
        )

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))
    return keyboard


def jobs_keyboard(jobs: list[Job], selected: list[int] = None) -> InlineKeyboardBuilder:
    """Клавиатура для выбора jobs"""
    keyboard = InlineKeyboardBuilder()

    for job in jobs:
        text = job.title

        if job.id in selected:
            text = "[ ✓ ] " + job.title

        keyboard.row(InlineKeyboardButton(
            text=f"{text}",
            callback_data=f"find_ex_job|{job.id}")
        )
    if selected:
        keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="find_ex_show|show_executors"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu|find_executor"))
    return keyboard


def executor_show_keyboard(is_last: bool) -> ReplyKeyboardMarkup:
    """Клавиатура для свайпов в демонстрации исполнителей"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=f"{btn.SKIP}"),
                KeyboardButton(text=f"{btn.TO_FAV}"),
                KeyboardButton(text=f"{btn.WRITE}")
            ],

        ],
        resize_keyboard=True,  # Автоматическое изменение размера
    )

    # Для последнего профиля
    if is_last:
        keyboard.one_time_keyboard = True   # Скрывает клавиатуру после использования

    return keyboard


def contact_with_executor(executor_tg_id: str) -> InlineKeyboardBuilder:
    """Клавиатура для связи с исполнителем"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.CONTACT_WITH}", callback_data=f"contact_with_ex|{executor_tg_id}"))
    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="cancel_executors_feed"))
    return keyboard


def back_to_executors_feed() -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"Вернуться к ленте", callback_data="cancel_executors_feed"))
    return keyboard