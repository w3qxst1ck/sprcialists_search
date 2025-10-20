from typing import List

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from routers.buttons import buttons as btn
from schemas.order import Order

from schemas.profession import Profession, Job
from settings import settings
from utils.datetime_service import get_days_in_month


def orders_menu(has_orders: bool) -> InlineKeyboardBuilder:
    """Клавиатура меню раздела Мои заказы"""
    keyboard = InlineKeyboardBuilder()

    # Если есть размещенные заказы
    if has_orders:
        keyboard.row(InlineKeyboardButton(text=f"Размещенные заказы", callback_data=f"my_orders_list"))

    keyboard.row(InlineKeyboardButton(text=f"Разместить заказ", callback_data=f"create_order"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu"))

    return keyboard


def my_orders_list_keyboard(orders: List[Order]) -> InlineKeyboardBuilder:
    """Клавиатура размещенных заказов для клиента"""
    keyboard = InlineKeyboardBuilder()

    for idx, order in enumerate(orders, start=1):
        keyboard.row(InlineKeyboardButton(text=f"{idx}", callback_data=f"my_order|{order.id}"))

    keyboard.adjust(3)

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="main_menu|my_orders"))

    return keyboard


def my_order_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура для манипуляций с заказом"""
    keyboard = InlineKeyboardBuilder()

    # Удалить заказ
    # keyboard.row(InlineKeyboardButton(text=f"Редактировать заказ", callback_data=f"edit_order|{order_id}"))
    keyboard.row(InlineKeyboardButton(text=f"Удалить заказ", callback_data=f"delete_order|{order_id}"))

    keyboard.row(InlineKeyboardButton(text=f"{btn.BACK}", callback_data="my_orders_list"))

    return keyboard


def delete_order_confirm_keyboard(order_id: int) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения удаления заказа"""
    keyboard = InlineKeyboardBuilder()

    # Удалить заказ
    keyboard.row(
        InlineKeyboardButton(text=f"Да", callback_data=f"delete_order_confirmed|{order_id}"),
        InlineKeyboardButton(text=f"Нет", callback_data=f"my_order|{order_id}"),
    )

    return keyboard


def profession_keyboard(professions: List[Profession]) -> InlineKeyboardBuilder:
    """Клавиатура с выбором профессии для создания заказа"""
    keyboard = InlineKeyboardBuilder()

    for profession in professions:
        keyboard.row(InlineKeyboardButton(text=f"{profession.title}", callback_data=f"choose_profession|{profession.id}"))

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def select_jobs_keyboard(jobs: List[Job], selected_jobs: List[int]) -> InlineKeyboardBuilder:
    """Клавиатура выбора Jobs с мультиселектом"""
    keyboard = InlineKeyboardBuilder()

    for job in jobs:
        title = job.title

        # Помечаем выбранные работы
        if job.id in selected_jobs:
            title = "[ ✓ ] " + title

        keyboard.row(InlineKeyboardButton(text=f"{title}", callback_data=f"select_jobs|{job.id}"))

    keyboard.adjust(2)

    # Подтвердить, если хотя бы одна Job выбрана
    if len(selected_jobs):
        keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="select_jobs_done"))

    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def calendar_keyboard(year: int, month: int, dates_data: dict, need_prev_month: bool) -> InlineKeyboardBuilder:
    """Клавиатура-календарь для выбора даты"""
    keyboard = InlineKeyboardBuilder()

    # получаем дни в месяце датами
    month_days = get_days_in_month(year, month)

    # заголовок клавиатуры
    header = f"🗓️ {settings.calendar_months[month]} {year}"
    keyboard.add(InlineKeyboardButton(text=header, callback_data="ignore"))

    # дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.row(*[InlineKeyboardButton(text=day, callback_data='ignore') for day in week_days])

    buttons = []

    # отступ для первого дня в месяце
    buttons += [InlineKeyboardButton(text=" ", callback_data="ignore")] * (month_days[0].weekday())

    # кнопки по дням месяца
    for d in month_days:
        callback = f"select_deadline|{d.day}.{d.month}.{d.year}"
        buttons.append(InlineKeyboardButton(text=str(d.day), callback_data=f'{callback}'))

    # отступ после последнего дня
    buttons += [InlineKeyboardButton(text=" ", callback_data="ignore")] * (6 - month_days[-1].weekday())

    # разбиваем по 7 штук в строке
    for i in range(0, len(buttons), 7):
        keyboard.row(*buttons[i:i + 7])

    # кнопки следующего месяца и предыдущего
    prev_month_name = settings.calendar_months[dates_data["prev_month"]]
    next_month_name = settings.calendar_months[dates_data["next_month"]]

    # Если нужен предыдущий месяц
    if need_prev_month:
        keyboard.row(
            InlineKeyboardButton(text=f"<< {prev_month_name} {dates_data['prev_year']}",
                                          callback_data=f"action|{dates_data['prev_month']}|{dates_data['prev_year']}"),
            InlineKeyboardButton(text=f"{next_month_name} {dates_data['next_year']} >>",
                                 callback_data=f"action|{dates_data['next_month']}|{dates_data['next_year']}")
        )
    # Если нужен только следующий
    else:
        keyboard.row(
            InlineKeyboardButton(text=" ", callback_data="ignore"),
            InlineKeyboardButton(text=f"{next_month_name} {dates_data['next_year']} >>",
                                 callback_data=f"action|{dates_data['next_month']}|{dates_data['next_year']}")
        )

    # Отменить
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def confirm_create_order_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура подтверждения создания заказа"""
    keyboard = InlineKeyboardBuilder()

    # Кнопка подтвердить
    keyboard.row(InlineKeyboardButton(text=f"Подтвердить", callback_data="confirm_create_order"))
    # Кнопка отмены
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def confirmed_create_order_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура после создания заказа"""
    keyboard = InlineKeyboardBuilder()

    # Кнопка Мои заказы
    keyboard.row(InlineKeyboardButton(text=f"{btn.MY_ORDERS}", callback_data=f"main_menu|my_orders"))

    return keyboard


def skip_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Пропустить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Пропустить", callback_data="skip"))
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def continue_cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура Продолжить/Отменить"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Продолжить", callback_data="continue"))
    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard


def cancel_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура отмены"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Отменить", callback_data="main_menu|my_orders"))

    return keyboard

