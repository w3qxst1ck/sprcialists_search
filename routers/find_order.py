from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_order as kb
from routers.keyboards.client_reg import to_main_menu
from routers.menu import main_menu
from routers.messages.find_executor import contact_with_client
from routers.messages.orders import order_card_to_show
from routers.states.find import SelectJobs, OrdersFeed
from routers.buttons import buttons as btn
from schemas.client import Client
from schemas.order import Order
from schemas.profession import Profession, Job
from utils.shuffle import shuffle_orders


router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data == "main_menu|find_order")
async def select_profession(callback: CallbackQuery, session: Any, state: FSMContext):
    """Выбор профессии для дальнейшего подбора заказа"""
    # Чистим стейт в случае нажатия кнопки назад
    try:
        await state.clear()
    except:
        pass

    # Получаем все профессии
    professions: list[Profession] = await AsyncOrm.get_professions(session)

    msg = "Выберите рубрику"
    keyboard = kb.professions_keyboard(professions)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "find_order_prof")
async def select_jobs_in_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Выбор jobs в выбранной профессии"""
    profession_id = int(callback.data.split("|")[1])

    # Получаем jobs для профессии
    jobs: list[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Устанавливаем стейт для мультиселекта
    await state.set_state(SelectJobs.jobs)

    # Записываем необходимые данные
    selected = []
    await state.update_data(jobs=jobs, selected=selected)

    msg = f"Выберите подкатегории для поиска"
    keyboard = kb.jobs_keyboard(jobs, selected)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "find_cl_job", SelectJobs.jobs)
async def pick_jobs(callback: CallbackQuery, state: FSMContext) -> None:
    """Мультиселект выбора jobs"""
    data = await state.get_data()
    jobs: list[Job] = data["jobs"]
    selected = data["selected"]

    # Получаем jobs (которую выбрали)
    selected_job_id = int(callback.data.split("|")[1])
    # Записываем в выбранные, а если уже была, то убираем ее от туда
    if selected_job_id in selected:
        selected.remove(selected_job_id)
    else:
        selected.append(selected_job_id)

    msg = f"Выберите подкатегории для поиска"
    keyboard = kb.jobs_keyboard(jobs, selected)

    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Обновляем данные с выбранными jobs
    await state.update_data(selected=selected)
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "find_cl_show|show_orders", SelectJobs.jobs)
async def end_multiselect(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Завершение мультиселекта и подбор подходящих заказов"""
    # Отправляем сообщение об ожидании
    wait_mess = await callback.message.edit_text(btn.WAIT_MSG)

    executor_tg_id: str = str(callback.from_user.id)

    # Получаем все данные
    data = await state.get_data()
    jobs_ids: list[int] = data["selected"]

    # Получаем список подходящих заказов
    orders: list[Order] = await AsyncOrm.get_orders_by_jobs(jobs_ids, session)
    is_last: bool = len(orders) == 1

    # Если заказов нет
    if not orders:
        # Очищаем стейт
        await state.clear()

        await wait_mess.edit_text(
            f"{btn.INFO} Подходящих заказов по вашему запросу не найдено, попробуйте выбрать больше рубрик",
            reply_markup=to_main_menu().as_markup()
        )
        return

    # Удаляем сообщение об ожидании
    try:
        await wait_mess.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(OrdersFeed.show)

    # Сортируем список в случайный порядок
    shuffled_orders: list[orders] = shuffle_orders(orders)

    # Получаем первый заказ
    order = shuffled_orders.pop()

    # Остальные заказы сохраняем в память
    await state.update_data(orders=shuffled_orders)
    # Записываем текущий заказ
    await state.update_data(current_or=order)

    # Проверяем есть ли у исполнителя этот заказ в избранном
    already_in_fav: bool = await check_is_order_in_favorites(executor_tg_id, order.id, session)

    # Выводим первый заказ
    msg = order_card_to_show(order, already_in_fav)
    keyboard = kb.order_show_keyboard(is_last)

    # Отправляем первый стартовый заказ
    await callback.message.answer(msg, reply_markup=keyboard)


# ПРОПУСТИТЬ
@router.message(F.text == f"{btn.SKIP}", OrdersFeed.show)
async def orders_feed(message: Message, state: FSMContext, session: Any) -> None:
    """Лента заказов при нажатии кнопки пропуск"""
    data = await state.get_data()
    executor_tg_id = str(message.from_user.id)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем заказы из памяти
    orders = data["orders"]
    is_last: bool = len(orders) == 1

    # Берем крайний
    try:
        order = orders.pop()

    # Если больше нет заказов
    except IndexError:
        # Очищаем стейт
        await state.clear()

        # Отправляем сообщение с главным меню
        await message.answer(f"{btn.INFO} Это все заказы по вашему запросу",
                             reply_markup=ReplyKeyboardRemove())    # убираем клавиатуру ReplyKeyboard
        await main_menu(message, session)
        return

    # Проверяем есть ли исполнитель уже в избранном
    already_in_fav: bool = await check_is_order_in_favorites(executor_tg_id, order.id, session)

    # Записываем оставшихся исполнителей обратно
    await state.update_data(orders=orders)
    # Записываем текущего исполнителя
    await state.update_data(current_or=order)

    msg = order_card_to_show(order, already_in_fav)
    keyboard = kb.order_show_keyboard(is_last)

    # Отправляем сообщение с заказом
    await message.answer(msg, reply_markup=keyboard)


# ДОБАВИТЬ В ИЗБРАННОЕ
@router.message(F.text == f"{btn.TO_FAV}", OrdersFeed.show)
async def add_order_to_favorites(message: Message, state: FSMContext, session: Any) -> None:
    """Лента заказов при нажатии кнопки избранное"""
    data = await state.get_data()
    executor_tg_id = str(message.from_user.id)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем id исполнителя
    executor_id: int = await AsyncOrm.get_executor_id(executor_tg_id, session)

    # Получаем текущий заказ
    order: Order = data["current_or"]
    # Получаем все заказы
    orders: list[Order] = data["orders"]

    # Проверяем есть ли он уже в исполнителях
    already_in_fav: bool = await check_is_order_in_favorites(executor_tg_id, order.id, session)
    if already_in_fav:
        await message.answer(f"{btn.INFO} Этот заказ уже есть у вас в списке избранных")
        # return

    else:
        # Сохраняем заказ в избранное у исполнителя
        try:
            await AsyncOrm.add_order_to_favorites(executor_id, order.id, session)
        except:
            await message.answer(f"Ошибка при добавлении заказа в избранное, попробуйте позже")
            return

        await message.answer("Заказ сохранен в ⭐ избранное")

    is_last: bool = len(orders) == 1
    msg = order_card_to_show(order, in_favorites=True)
    keyboard = kb.order_show_keyboard(is_last)

    # Отправляем сообщение с заказом
    await message.answer(msg, reply_markup=keyboard)


# НАПИСАТЬ ЗАКАЗЧИКУ
@router.message(F.text == f"{btn.WRITE}", OrdersFeed.show)
async def connect_with_client(message: Message, state: FSMContext, session: Any) -> None:
    """Связаться с заказчиком"""
    data = await state.get_data()

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем текущий заказ
    order: Order = data["current_or"]
    # Получаем username заказчика для формирования ссылки
    tg_username: str = await AsyncOrm.get_username(order.tg_id, session)
    client: Client = await AsyncOrm.get_client(order.tg_id, session)

    msg = contact_with_client(tg_username, client)
    keyboard = kb.contact_with_client()

    functional_mess = await message.answer(msg, reply_markup=keyboard.as_markup())
    await state.update_data(functional_mess=functional_mess)


# ВОЗВРАЩЕНИЕ ИЗ РАЗНЫХ ТОЧЕК В ЛЕНТУ ЗАКАЗОВ
@router.callback_query(F.data == "back_to_orders_feed", OrdersFeed.show)
async def back_to_orders_feed(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Для возвращения в ленту из ответвлений"""
    data = await state.get_data()
    executor_tg_id: str = str(callback.from_user.id)

    # Удаляем предыдущее сообщение
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем текущего исполнителя
    order: Order = data["current_or"]

    # Получаем исполнителей из памяти
    orders: list[Order] = data["orders"]
    is_last: bool = len(orders) == 1
    already_in_fav = await check_is_order_in_favorites(executor_tg_id, order.id, session)

    msg = order_card_to_show(order, already_in_fav)
    keyboard = kb.order_show_keyboard(is_last)

    await callback.message.answer(msg, reply_markup=keyboard)


async def check_is_order_in_favorites(executor_tg_id: str, order_id: int, session: Any) -> bool:
    """Возвращает true если заказ есть в избранных исполнителя, иначе false"""
    already_in_fav: bool = await AsyncOrm.is_order_already_in_favorites(executor_tg_id, order_id, session)
    return already_in_fav
