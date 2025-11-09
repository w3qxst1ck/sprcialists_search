from typing import Any

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.keyboards import favorites as kb
from routers.keyboards.client_reg import to_main_menu
from routers.menu import main_menu
from routers.messages.executor import executor_profile_to_show
from routers.messages.find_executor import contact_with_executor
from routers.states.favorites import FavoriteExecutors

from schemas.executor import Executor

from logger import logger
from settings import settings

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data.split("|")[1] == "client_favorites")
async def favorites_executors(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Выводит избранных исполнителей для клиента"""
    # Отправляем сообщение об ожидании
    wait_mess = await callback.message.edit_text(f"{btn.WAIT_MSG}")

    client_tg_id = str(callback.from_user.id)

    # Начинаем state
    await state.set_state(FavoriteExecutors.feed)

    # Получаем избранных исполнителей у клиента
    executors: list[Executor] = await AsyncOrm.get_favorites_executors(client_tg_id, session)
    current_index = 0

    # Записываем в стейт всех исполнителей и текущего
    await state.update_data(
        executors=executors,
        current_index=current_index
    )

    # Удаляем сообщение об ожидании
    try:
        await wait_mess.delete()
    except:
        pass

    # Отправляем сообщение с профилем
    await send_executor_profile(executors, current_index, callback, state, is_first=True)


@router.callback_query(or_f(F.data == "prev_ex", F.data == "next_ex"), FavoriteExecutors.feed)
async def show_executor(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает следующего или предыдущего исполнителя"""
    data = await state.get_data()
    current_index = data["current_index"]
    executors = data["executors"]
    prev_mess = data["prev_mess"]

    # При нажатии влево
    if callback.data == "prev_ex":
        # Меняем текущий индекс
        if current_index == 0:
            current_index = len(executors) - 1
        else:
            current_index -= 1

    # При нажатии вправо
    elif callback.data == "next_ex":
        # Меняем текущий индекс
        if current_index == len(executors) - 1:
            current_index = 0
        else:
            current_index += 1

    # Сохраняем текущий индекс
    await state.update_data(current_index=current_index)
    # Отправляем сообщение
    await send_executor_profile(executors, current_index, prev_mess, state)


@router.callback_query(F.data.split("|")[0] == "write_fav_ex", FavoriteExecutors.feed)
async def write_to_fav_executor(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    data = await state.get_data()

    # Получаем данные для формирования сообщения
    current_index = data["current_index"]
    executors = data["executors"]
    executor = executors[current_index]

    ex_username = await AsyncOrm.get_username(executor.tg_id, session)

    ms = contact_with_executor(executor, ex_username)
    keyboard = kb.back_to_feed_keyboard()

    # Удаляем предыдудщее сообщение
    try:
        await data["prev_mess"].delete()
    except Exception as e:
        print(e)

    prev_mess = await callback.message.answer(ms, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)

    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "back_to_fav_feed", FavoriteExecutors.feed)
async def back_to_favorites_feed(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Возвращение в ленту избранных"""
    data = await state.get_data()

    executors = data["executors"]
    current_index = data["current_index"]

    try:
        await data["prev_mess"].delete()
    except:
        pass

    await send_executor_profile(executors, current_index, callback, state, is_first=True)


@router.callback_query(F.data == "back_from_favorites_feed", FavoriteExecutors.feed)
async def back_from_favorites_feed(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Возвращение из ленты избранных"""
    data = await state.get_data()

    # Удаляем сообщение
    try:
        await data["prev_mess"].delete()
    except:
        pass

    # Очищаем стейт
    await state.clear()

    # Переводим в главное меню
    await main_menu(callback, session)


@router.callback_query(F.data.split("|")[0] == "delete_fav", FavoriteExecutors.feed)
async def delete_from_favorite(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Удаление исполнителя из списка избранных у клиента"""
    client_tg_id = str(callback.from_user.id)
    executor_id = int(callback.data.split("|")[1])
    data = await state.get_data()

    # Удаляем предыдущее сообщение
    try:
        await data["prev_mess"].delete()
    except:
        pass

    # Удаляем исполнителя из избранных в БД
    try:
        await AsyncOrm.delete_executor_from_favorites(client_tg_id, executor_id, session)
    except:
        await callback.message.answer(f"{btn.INFO} Ошибка при удалении исполнителя из избранных, попробуйте еще раз позже")
        return

    prev_mess = await callback.message.answer(f"{btn.SUCCESS} Исполнитель удален из избранных")

    # Формируем данные для новой ленты исполнителей
    executors = data["executors"]

    # Удаляем из стейта этого исполнителя
    for executor in executors:
        if executor.id == executor_id:
            executors.remove(executor)

    # Обновляем список исполнителей
    current_index = 0  # обнуляем текущий индекс
    await state.update_data(
        executors=executors,
        current_index=current_index
    )

    # Отправляем ленту
    await send_executor_profile(executors, current_index, prev_mess, state, is_first=True)


async def send_executor_profile(executors: list[Executor], current_index: int, prev_mess: Message | CallbackQuery,
                                state: FSMContext, is_first: bool = False) -> None:
    """Отправка сообщения с карточкой исполнителя"""
    # Если еще нет исполнителей или их удалили в ленте
    if len(executors) == 0:
        # Если исполнитель был 1 и его удалили
        msg = "У тебя еще нет избранных исполнителей"
        keyboard = kb.back_keyboard()

        if isinstance(prev_mess, CallbackQuery):
            await prev_mess.message.answer(msg, reply_markup=keyboard.as_markup())
        else:
            await prev_mess.answer(msg, reply_markup=keyboard.as_markup())
            await prev_mess.delete()
        return

    executor = executors[current_index]

    # Формируем сообщение
    msg = executor_profile_to_show(executors[current_index])
    keyboard = kb.favorites_executor_keyboard(executors, current_index)

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        # берем дефолтную, если нет фотографии пользователя
        filepath = settings.local_media_path + f"executor.jpg"
    try:
        profile_image = FSInputFile(filepath)

        # Для отправки первого сообщения в ленте
        if is_first:
            if isinstance(prev_mess, CallbackQuery):
                prev_mess = await prev_mess.message.answer_photo(
                    photo=profile_image,
                    caption=msg,
                    reply_markup=keyboard.as_markup(),
                    disable_web_page_preview=True
                )
            else:
                prev_mess = await prev_mess.answer_photo(
                    photo=profile_image,
                    caption=msg,
                    reply_markup=keyboard.as_markup(),
                    disable_web_page_preview=True
                )
        # Для всех последующих
        else:
            prev_mess = await prev_mess.edit_caption(
                photo=profile_image,
                caption=msg,
                reply_markup=keyboard.as_markup(),
                disable_web_page_preview=True
            )

        await state.update_data(prev_mess=prev_mess)

    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")
        msg = f"Сервис временно недоступен, попробуйте позже или обратитесь " \
              f"к администратору @{settings.admin_tg_username}"
        keyboard = to_main_menu()
        await prev_mess.answer(msg, reply_markup=keyboard.as_markup())
