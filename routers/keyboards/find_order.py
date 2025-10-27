from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


from routers.buttons import buttons as btn
from schemas.profession import Job, Profession


def professions_keyboard(professions: list[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура для выбора профессии"""
    keyboard = InlineKeyboardBuilder()

    for prof in professions:
        keyboard.row(InlineKeyboardButton(
            text=f"{prof.title}",
            callback_data=f"find_order_prof|{prof.id}")
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
            callback_data=f"find_cl_job|{job.id}")
        )
    if selected:
        keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="find_cl_show|show_orders"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu|find_order"))
    return keyboard


def order_show_keyboard(is_last: bool) -> ReplyKeyboardMarkup:
    """Клавиатура для свайпов в демонстрации заказов"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=f"{btn.SKIP}"),
                KeyboardButton(text=f"{btn.TO_FAV}"),
                KeyboardButton(text=f"{btn.RESPOND}")
            ],

        ],
        resize_keyboard=True,  # Автоматическое изменение размера
    )

    # Для последнего профиля
    if is_last:
        keyboard.one_time_keyboard = True   # Скрывает клавиатуру после использования

    return keyboard


def confirm_send_cover_letter() -> InlineKeyboardBuilder:
    """Клавиатура для подтверждения отправки сопроводительного письма"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"{btn.SEND_COVER_LETTER}", callback_data="send_cover_letter"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.CANCEL}", callback_data="back_to_orders_feed"))
    return keyboard


def back_to_orders_feed() -> InlineKeyboardBuilder:
    """Клавиатура для возвращения в ленту"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="back_to_orders_feed"))
    return keyboard


def back_to_orders_feed_from_contact() -> InlineKeyboardBuilder:
    """Клавиатура для возвращения в ленту"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK_TO_FEED}", callback_data="back_to_orders_feed"))
    return keyboard
