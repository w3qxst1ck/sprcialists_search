from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaDocument

from logger import logger
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.keyboards import favorites as kb
from routers.keyboards.client_reg import to_main_menu
from routers.messages.find_order import contact_with_client, response_on_order_message
from routers.messages.orders import order_card_to_show
from routers.states.favorites import FavoriteOrders
from schemas.client import Client
from schemas.executor import Executor
from schemas.order import Order


router = Router()

# router.message.middleware.register(DatabaseMiddleware())
# router.callback_query.middleware.register(DatabaseMiddleware())

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

    # Если пользователь не верифицирован
    if not executor.verified:
        msg = "Данный функционал доступен только верифицированным пользователям"
        keyboard = to_main_menu()

        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
        return

    # Начинаем state
    await state.set_state(FavoriteOrders.feed)

    # Получаем избранных исполнителей у клиента
    orders: list[Order] = await AsyncOrm.get_favorites_orders(executor.id, session)

    # Если заказов пока нет
    if not orders:
        msg = "У тебя еще нет избранных заказов"
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
    try:
        await send_order_card(orders, current_index, prev_mess, state)
    except:
        pass


# Написать заказчику
@router.callback_query(F.data.split("|")[0] == "write_fav_order", FavoriteOrders.feed)
async def write_to_client_from_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    """Написать заказчику из избранного"""
    data = await state.get_data()

    orders: list[Order] = data["orders"]
    order: Order = orders[data["current_index"]]

    await state.set_state(FavoriteOrders.contact)

    msg = f"Заказ <b>\"{order.title}\"</b>\n\nОтправь в чат сопроводительный текст, который будет отправлен заказчику " \
          f"вместе с твоим откликом"
    keyboard = kb.back_to_feed_keyboard()

    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup(),
                                                       disable_web_page_preview=True)
    await state.update_data(prev_mess=prev_mess)


@router.message(FavoriteOrders.contact)
async def get_cover_letter(message: Message, state: FSMContext) -> None:
    """Получение сопроводительного письма от исполнителя"""
    data = await state.get_data()

    #  Удаляем предыдущее сообщение если было
    try:
        await data["prev_mess"].delete()
    except:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                               reply_markup=kb.back_to_feed_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем стейт на подтверждение отправки
    await state.set_state(FavoriteOrders.send_confirm)

    cover_letter = message.text

    msg = f"Твой отклик:\n\n<i>\"{cover_letter}\"</i>\n\nОтправляем?"
    keyboard = kb.confirm_send_cover_letter()
    await message.answer(msg, reply_markup=keyboard.as_markup())

    # Сохраняем текст сопроводительного письма в память
    await state.update_data(cover_letter=cover_letter)


@router.callback_query(F.data == "send_cover_letter", FavoriteOrders.send_confirm)
async def send_cover_letter(callback: CallbackQuery, state: FSMContext, session: Any, bot: Bot) -> None:
    """Отправка сопроводительного письма с откликом"""
    await callback.answer()

    data = await state.get_data()

    # Данные исполнителя
    executor_tg_id = str(callback.from_user.id)
    ex_tg_username = await AsyncOrm.get_username(executor_tg_id, session)
    ex_name = await AsyncOrm.get_executor_name(executor_tg_id, session)

    # Получаем заказ и сопроводительное письмо
    orders: list[Order] = data["orders"]
    order: Order = orders[data["current_index"]]
    cover_letter = data["cover_letter"]

    msg = f"{btn.SUCCESS} Твой отклик по заказу \"<i>{order.title}</i>\" отправлен заказчику!"
    keyboard = kb.back_to_feed_keyboard()

    # Отвечаем исполнителю
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Отправляем сообщение клиенту
    msg_to_client = response_on_order_message(cover_letter, order, ex_tg_username, ex_name)
    try:
        await bot.send_message(order.tg_id, msg_to_client,
                               message_effect_id="5104841245755180586",     # 🔥
                               disable_web_page_preview=True
                               )

    except Exception as e:
        logger.error(f"Ошибка при отправке отклика заказчику по заказу {order.id} от {executor_tg_id}: {e}")


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
@router.callback_query(F.data == "back_to_fav_feed",
                       StateFilter(FavoriteOrders.feed, FavoriteOrders.contact, FavoriteOrders.send_confirm))
async def back_to_current_feed(callback: CallbackQuery, state: FSMContext) -> None:
    """Выводим текущий заказ в ленте"""
    current_state = await state.get_state()

    if current_state != FavoriteOrders.feed:
        await state.set_state(FavoriteOrders.feed)

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
        msg = "У тебя еще нет избранных заказов"
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
            # Если пришли после скачивания файлов
            if message.data.split("|")[0] == "files_for_order":
                prev_mess = await message.message.answer(msg, reply_markup=keyboard.as_markup())
            else:
                prev_mess = await message.message.edit_text(msg, reply_markup=keyboard.as_markup())

    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "files_for_order")
async def download_files(callback: CallbackQuery, state: FSMContext) -> None:
    """Отправка пользователю файлов заказа"""
    # Удаляем предыдущее сообщение
    try:
        await callback.answer()
        await callback.message.edit_text(callback.message.text)
    except:
        pass

    data = await state.get_data()

    orders = data["orders"]
    current_index = data["current_index"]

    # Получаем заказ
    order = orders[current_index]

    # Отправляем файлы
    files = [InputMediaDocument(media=file.file_id) for file in order.files]
    try:
        await callback.message.answer_media_group(media=files)
    except Exception:
        await callback.message.answer(f"{btn.INFO} Ошибка при отправке файлов. Повторите запрос позже")
    finally:
        await send_order_card(orders, current_index, callback, state, is_first=False)


