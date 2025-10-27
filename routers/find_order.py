from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, InputMediaDocument

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_order as kb
from routers.keyboards.client_reg import to_main_menu
from routers.menu import main_menu
from routers.messages.orders import order_card_to_show
from routers.messages import find_order as ms
from routers.states.find import SelectJobs, OrdersFeed
from routers.buttons import buttons as btn
from schemas.order import Order
from schemas.profession import Profession, Job
from utils.shuffle import shuffle_orders

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

    await callback.answer()
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

    await callback.answer()
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

    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Обновляем данные с выбранными jobs
    await state.update_data(selected=selected)
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "find_cl_show|show_orders", SelectJobs.jobs)
async def end_multiselect(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Завершение мультиселекта и подбор подходящих заказов"""
    # Убираем загрузку
    await callback.answer()
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

    # Если есть файлы отправляем их после заказа
    if order.files:
        files = [InputMediaDocument(media=file.file_id) for file in order.files]
        try:
            await callback.message.answer_media_group(media=files)
        except:
            pass


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

    # Если есть файлы отправляем их после заказа
    if order.files:
        files = [InputMediaDocument(media=file.file_id) for file in order.files]
        try:
            await message.answer_media_group(media=files)
        except:
            pass


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

    # Если есть файлы отправляем их после заказа
    if order.files:
        files = [InputMediaDocument(media=file.file_id) for file in order.files]
        try:
            await message.answer_media_group(media=files)
        except:
            pass


# НАПИСАТЬ ЗАКАЗЧИКУ
@router.message(F.text == f"{btn.RESPOND}", OrdersFeed.show)
async def connect_with_client(message: Message, state: FSMContext) -> None:
    """Связаться с заказчиком"""
    data = await state.get_data()

    # Меняем стейт для связи с заказчиком
    await state.set_state(OrdersFeed.contact)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем текущий заказ
    order: Order = data["current_or"]

    msg = f"Заказ <b>\"{order.title}\"</b>\n\nОтправьте в чат сопроводительный текст, который будет отправлен заказчику " \
          f"вместе с вашим откликом"

    keyboard = kb.back_to_orders_feed()

    functional_mess = await message.answer(msg, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)
    await state.update_data(functional_mess=functional_mess)


@router.message(OrdersFeed.contact)
async def get_cover_letter(message: Message, state: FSMContext) -> None:
    """Получение сопроводительного письма от исполнителя"""
    data = await state.get_data()

    #  Удаляем предыдущее сообщение если было
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Если отправлен не текст
    if not message.text:
        functional_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.back_to_orders_feed().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(functional_mess=functional_mess)
        return

    # Игнорируем текст от кнопок
    if message.text in (btn.RESPOND, btn.SKIP, btn.TO_FAV):
        functional_mess = await message.answer("Напишите другой текст",
                                         reply_markup=kb.back_to_orders_feed().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(functional_mess=functional_mess)
        return

    # Меняем стейт на подтверждение отправки
    await state.set_state(OrdersFeed.confirm_send)

    cover_letter = message.text

    msg = f"Ваш отклик:\n\n<i>\"{cover_letter}\"</i>\n\nОтправляем?"
    keyboard = kb.confirm_send_cover_letter()

    functional_mess = await message.answer(msg, reply_markup=keyboard.as_markup())
    await state.update_data(functional_mess=functional_mess)

    # Сохраняем текст сопроводительного письма в память
    await state.update_data(cover_letter=cover_letter)


@router.callback_query(OrdersFeed.confirm_send, F.data == "send_cover_letter")
async def send_cover_letter(callback: CallbackQuery, state: FSMContext, session: Any, bot: Bot) -> None:
    """Отправка сопроводительного письма с откликом"""
    await callback.answer()

    data = await state.get_data()
    executor_tg_id = str(callback.from_user.id)
    ex_tg_username = await AsyncOrm.get_username(executor_tg_id, session)
    ex_name = await AsyncOrm.get_executor_name(executor_tg_id, session)

    # Получаем заказ
    order: Order = data["current_or"]
    cover_letter = data["cover_letter"]

    msg = f"{btn.SUCCESS} Ваш отклик по заказу \"<i>{order.title}</i>\" отправлен заказчику!"
    keyboard = kb.back_to_orders_feed_from_contact()

    # Отвечаем исполнителю
    functional_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
    await state.update_data(functional_mess=functional_mess)

    msg_to_client = ms.response_on_order_message(cover_letter, order, ex_tg_username, ex_name)

    # Отправляем сообщение клиенту
    try:
        # await bot.send_message(order.tg_id, msg_to_client, message_effect_id="5104841245755180586", disable_web_page_preview=True)    # 🔥
        await bot.send_message("420551454", msg_to_client,
                               message_effect_id="5104841245755180586",
                               disable_web_page_preview=True)    # TODO DEV VER

    except Exception as e:
        logger.error(f"Ошибка при отправке отклика заказчику по заказу {order.id} от {executor_tg_id}: {e}")


# ВОЗВРАЩЕНИЕ ИЗ РАЗНЫХ ТОЧЕК В ЛЕНТУ ЗАКАЗОВ
@router.callback_query(StateFilter(OrdersFeed.show, OrdersFeed.contact, OrdersFeed.confirm_send),
                       F.data == "back_to_orders_feed")
async def back_to_orders_feed(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Для возвращения в ленту из ответвлений"""
    data = await state.get_data()
    executor_tg_id: str = str(callback.from_user.id)

    await callback.answer()

    # Меняем стейт на показ ленты
    await state.set_state(OrdersFeed.show)

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

    # Если есть файлы отправляем их после заказа
    if order.files:
        files = [InputMediaDocument(media=file.file_id) for file in order.files]
        try:
            await callback.message.answer_media_group(media=files)
        except:
            pass


async def check_is_order_in_favorites(executor_tg_id: str, order_id: int, session: Any) -> bool:
    """Возвращает true если заказ есть в избранных исполнителя, иначе false"""
    already_in_fav: bool = await AsyncOrm.is_order_already_in_favorites(executor_tg_id, order_id, session)
    return already_in_fav
