from typing import Any

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaDocument

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.keyboards import favorites as kb
from routers.messages.find_executor import contact_with_client
from routers.messages.orders import order_card_to_show
from routers.states.favorites import FavoriteOrders
from schemas.client import Client
from schemas.executor import Executor
from schemas.order import Order


router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data.split("|")[1] == "executor_favorites")
async def favorites_orders(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Выводит избранные заказы для исполнителя"""
    # Отправляем сообщение об ожидании
    await callback.answer()
    wait_mess = await callback.message.edit_text(f"{btn.WAIT_MSG}")

    executor_tg_id = str(callback.from_user.id)
    executor: Executor = await AsyncOrm.get_executor_by_tg_id(executor_tg_id, session)

    # Начинаем state
    await state.set_state(FavoriteOrders.feed)

    # Получаем избранных исполнителей у клиента
    orders: list[Order] = await AsyncOrm.get_favorites_orders(executor.id, session)

    # Если заказов пока нет
    if not orders:
        msg = "У вас еще нет избранных заказов"
        keyboard = kb.back_keyboard()
        await wait_mess.edit_text(msg, reply_markup=keyboard.as_markup())
        return

    current_index = 0

    # Записываем в стейт все заказы и текущий
    await state.update_data(
        orders=orders,
        current_index=current_index
    )

    # Удаляем сообщение об ожидании
    try:
        await wait_mess.delete()
    except:
        pass

    # Отправляем сообщение с профилем
    await send_order_card(orders, current_index, callback, state, is_first=True)


# Для листания вправо, влево
@router.callback_query(or_f(F.data == "prev", F.data == "next"), FavoriteOrders.feed)
async def show_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает следующий или предыдущий заказ"""
    data = await state.get_data()
    current_index = data["current_index"]
    orders = data["orders"]
    prev_mess = data["prev_mess"]

    # При нажатии влево
    if callback.data == "prev":
        # Меняем текущий индекс
        if current_index == 0:
            current_index = len(orders) - 1
        else:
            current_index -= 1

    # При нажатии вправо
    elif callback.data == "next":
        # Меняем текущий индекс
        if current_index == len(orders) - 1:
            current_index = 0
        else:
            current_index += 1

    # Сохраняем текущий индекс
    await state.update_data(current_index=current_index)
    # Отправляем сообщение
    await send_order_card(orders, current_index, prev_mess, state)


# Написать заказчику
@router.callback_query(F.data.split("|")[0] == "write_fav_order", FavoriteOrders.feed)
async def write_to_client_from_favorite(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Написать заказчику из избранного"""
    data = await state.get_data()

    orders: list[Order] = data["orders"]
    order: Order = orders[data["current_index"]]

    client_username: str = await AsyncOrm.get_username(order.tg_id, session)
    client: Client = await AsyncOrm.get_client(order.tg_id, session)

    ms = contact_with_client(client_username, client)
    keyboard = kb.back_to_feed_keyboard()

    await callback.answer()
    await callback.message.edit_text(ms, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)


# Удалить из избранного
@router.callback_query(F.data.split("|")[0] == "delete_fav_order", FavoriteOrders.feed)
async def delete_from_favorite(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Удаление заказа из списка избранных у исполнителя"""
    executor_tg_id = str(callback.from_user.id)
    order_id = int(callback.data.split("|")[1])
    data = await state.get_data()

    # Удаляем предыдущее сообщение
    try:
        await data["prev_mess"].delete()
    except:
        pass

    # Удаляем исполнителя из избранных в БД
    try:
        await AsyncOrm.delete_order_from_favorites(executor_tg_id, order_id, session)
    except:
        await callback.message.answer(f"{btn.INFO} Ошибка при удалении заказа из избранных, попробуйте еще раз позже")
        return

    prev_mess = await callback.message.answer(f"{btn.SUCCESS} Заказ удален из избранных")

    # Формируем данные для новой ленты исполнителей
    orders = data["orders"]

    # Удаляем из стейта этого исполнителя
    for order in orders:
        if order.id == order_id:
            orders.remove(order)

    # Обновляем список исполнителей
    current_index = 0  # обнуляем текущий индекс
    await state.update_data(
        orders=orders,
        current_index=current_index
    )

    # Отправляем ленту
    await send_order_card(orders, current_index, prev_mess, state, is_first=True)


# Для отлавливания кнопок назад и отправки текущей ленты
@router.callback_query(F.data == "back_to_fav_feed", FavoriteOrders.feed)
async def back_to_current_feed(callback: CallbackQuery, state: FSMContext) -> None:
    """Выводим текущий заказ в ленте"""
    data = await state.get_data()

    orders: list[Order] = data["orders"]
    current_index = data["current_index"]

    await send_order_card(orders, current_index, callback, state)


# Универсальная отправка карточки заказа
async def send_order_card(orders: list[Order], current_index: int, message: CallbackQuery | Message,
                          state: FSMContext, is_first: bool = False) -> None:
    """Отправка сообщения с карточкой заказа"""
    # Если еще нет исполнителей или их удалили в ленте
    if len(orders) == 0:
        # Если заказ был 1 и его удалили
        msg = "У вас еще нет избранных заказов"
        keyboard = kb.back_keyboard()

        if isinstance(message, Message):
            try:
                await message.edit_text(msg, reply_markup=keyboard.as_markup())
            except:
                await message.answer(msg, reply_markup=keyboard.as_markup())
        else:
            await message.answer()
            await message.message.edit_text(msg, reply_markup=keyboard.as_markup())
        return

    # Получаем отображаемый заказ
    order = orders[current_index]

    # Формируем сообщение
    msg = order_card_to_show(order)
    keyboard = kb.favorites_orders_keyboard(orders, current_index)

    # Отправляем карточки заказа
    if is_first:
        if isinstance(message, Message):
            prev_mess = await message.answer(msg, reply_markup=keyboard.as_markup())
        else:
            prev_mess = await message.message.answer(msg, reply_markup=keyboard.as_markup())
    else:
        if isinstance(message, Message):
            prev_mess = await message.edit_text(msg, reply_markup=keyboard.as_markup())
        else:
            await message.answer()
            prev_mess = await message.message.edit_text(msg, reply_markup=keyboard.as_markup())

    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "files_for_order")
async def download_files(callback: CallbackQuery, session: Any) -> None:
    """Отправка пользователю файлов заказа"""
    # Удаляем предыдущее сообщение
    # try:
    #     await callback.message.delete()
    # except:
    #     pass

    # Получаем заказ
    order_id = int(callback.data.split("|")[1])
    order: Order = await AsyncOrm.get_order_by_id(order_id, session)

    # Отправляем файлы
    files = [InputMediaDocument(media=file.file_id) for file in order.files]
    try:
        await callback.message.answer_media_group(media=files)
    except Exception:
        await callback.message.answer(f"{btn.INFO} Ошибка при отправке файлов. Повторите запрос позже")
    # finally:
    #     TODO
    #     send_order_card

