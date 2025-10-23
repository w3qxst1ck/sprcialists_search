from typing import Any

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_order as kb
from routers.keyboards.client_reg import to_main_menu
from routers.messages.orders import order_card_to_show
from routers.states.find import SelectJobs, OrdersFeed
from routers.buttons import buttons as btn
from schemas.order import Order
from schemas.profession import Profession, Job
from utils.shuffle import shuffle_orders

from settings import settings
from logger import logger

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


@router.callback_query(F.data.split("|")[0] == "find_cl_prof")
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

    # Если исполнителей нет
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

    # Получаем фото
    await callback.message.answer(msg, reply_markup=keyboard)


async def check_is_order_in_favorites(executor_tg_id: str, order_id: int, session: Any) -> bool:
    """Возвращает true если заказ есть в избранных исполнителя, иначе false"""
    return False # TODO DEV VERSION