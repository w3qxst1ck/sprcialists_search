from aiogram.types import InlineKeyboardButton
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
            text = "[ ✓ ]" + job.title

        keyboard.row(InlineKeyboardButton(
            text=f"{text}",
            callback_data=f"find_ex_job|{job.id}")
        )
    if selected:
        keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="find_ex_show|show_executors"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu|find_executor"))
    return keyboard


