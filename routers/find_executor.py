from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, InputFile, ReplyKeyboardRemove

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_executor as kb
from routers.keyboards.client_reg import to_main_menu
from routers.menu import main_menu
from routers.messages.executor import executor_profile_to_show
from routers.messages import find_executor as ms
from routers.states.find import SelectJobs, ExecutorsFeed
from routers.buttons import buttons as btn
from schemas.client import Client
from schemas.profession import Profession, Job
from schemas.executor import Executor
from utils.shuffle import shuffle_executors

from settings import settings
from logger import logger

router = Router()

# router.message.middleware.register(DatabaseMiddleware())
# router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data == "main_menu|find_executor")
async def select_profession(callback: CallbackQuery, session: Any, state: FSMContext):
    """Выбор профессии для дальнейшего подбора исполнителя"""
    # Чистим стейт в случае нажатия кнопки назад
    try:
        await state.clear()
    except:
        pass

    # Получаем все профессии
    professions: list[Profession] = await AsyncOrm.get_professions(session)

    msg = "Выбери направление"
    keyboard = kb.professions_keyboard(professions)

    await callback.answer()  # Убирает "загрузку"
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "find_ex_prof")
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

    msg = "Выбери категории (до 3 вариантов)"
    keyboard = kb.jobs_keyboard(jobs, selected)

    await callback.answer()  # Убирает "загрузку"
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "find_ex_job", SelectJobs.jobs)
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
        if len(selected) == 3:
            selected[0] = selected_job_id
        else:
            selected.append(selected_job_id)

    msg = "Выбери категории (до 3 вариантов)"
    keyboard = kb.jobs_keyboard(jobs, selected)

    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Обновляем данные с выбранными jobs
    await state.update_data(selected=selected)
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "find_ex_show|show_executors", SelectJobs.jobs)
@router.callback_query(F.data == "find_ex_show|show_executors", ExecutorsFeed.show)     # Для повторного показа
async def end_multiselect(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Завершение мультиселекта и подбор подходящих исполнителей"""
    # Отправляем сообщение об ожидании
    wait_mess = await callback.message.edit_text(btn.WAIT_MSG)

    client_tg_id: str = str(callback.from_user.id)

    # Получаем все данные
    data = await state.get_data()
    jobs_ids: list[int] = data["selected"]

    # Получаем список подходящих исполнителей
    executors: list[Executor] = await AsyncOrm.get_executors_by_jobs(jobs_ids, session)
    is_last: bool = len(executors) == 1

    # Если исполнителей нет
    if not executors:
        # Очищаем стейт
        await state.clear()

        await wait_mess.edit_text(
            f"😔 Исполнителей по твоему запросу не найдено. Попробуй указать больше категорий или выбрать другое направление",
            reply_markup=to_main_menu().as_markup()
        )
        # await main_menu(callback, session)
        return

    # Меняем сообщение об ожидании на инструкцию
    try:
        await wait_mess.edit_text(ms.instruction_msg())
    except:
        pass

    # Меняем стейт
    await state.set_state(ExecutorsFeed.show)

    # Сортируем список в случайный порядок
    shuffled_executors: list[Executor] = shuffle_executors(executors)

    # Получаем первого исполнителя
    executor = shuffled_executors.pop()

    # Остальных исполнителей сохраняем в память
    await state.update_data(executors=shuffled_executors)
    # Записываем текущего исполнителя
    await state.update_data(current_ex=executor)

    # Проверяем есть ли исполнитель уже в избранном
    already_in_fav: bool = await check_is_executor_in_favorites(client_tg_id, executor.id, session)

    # Выводим первого исполнителя
    msg = executor_profile_to_show(executor, already_in_fav)
    keyboard = kb.executor_show_keyboard(is_last)

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        # берем дефолтную, если нет фотографии пользователя
        filepath = settings.local_media_path + f"executor.jpg"
    try:
        profile_image = FSInputFile(filepath)

        await callback.message.answer_photo(
            photo=profile_image,
            caption=msg,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        await callback.answer()  # Убираем "часики" у кнопки

    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")
        msg = f"Сервис временно недоступен, попробуй позже или обратись к администратору @{settings.admin_tg_username}"
        keyboard = to_main_menu()
        await callback.message.answer(msg, reply_markup=keyboard.as_markup())


# ПРОПУСТИТЬ
@router.message(F.text == f"{btn.SKIP}", ExecutorsFeed.show)
async def executors_feed(message: Message, state: FSMContext, session: Any) -> None:
    """Лента исполнителей при нажатии кнопки пропуск"""
    data = await state.get_data()
    client_tg_id = str(message.from_user.id)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем исполнителей из памяти
    executors = data["executors"]
    is_last: bool = len(executors) == 1

    # Берем крайнего
    try:
        executor = executors.pop()

    # Если больше нет исполнителей
    except IndexError:
        # Очищаем стейт
        # await state.clear()

        # Отправляем сообщение с главным меню
        await message.answer(f"{btn.INFO} Это все исполнители по твоему запросу",
                             reply_markup=ReplyKeyboardRemove())    # убираем клавиатуру ReplyKeyboard
        await message.answer("Посмотреть найденных исполнителей еще раз?",
                             reply_markup=kb.show_again_or_main_menu_keyboard().as_markup())
        # await main_menu(message, session)
        return

    # Проверяем есть ли исполнитель уже в избранном
    already_in_fav: bool = await check_is_executor_in_favorites(client_tg_id, executor.id, session)

    # Записываем оставшихся исполнителей обратно
    await state.update_data(executors=executors)
    # Записываем текущего исполнителя
    await state.update_data(current_ex=executor)

    msg = executor_profile_to_show(executor, already_in_fav)
    keyboard = kb.executor_show_keyboard(is_last)

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        # берем дефолтную, если нет фотографии пользователя
        filepath = settings.local_media_path + f"executor.jpg"
    try:
        profile_image = FSInputFile(filepath)

        await message.answer_photo(
            photo=profile_image,
            caption=msg,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")
        msg = f"Сервис временно недоступен, попробуй позже или обратись к администратору @{settings.admin_tg_username}"
        keyboard = to_main_menu()
        await message.answer(msg, reply_markup=keyboard.as_markup())


# ДОБАВИТЬ В ИЗБРАННОЕ
@router.message(F.text == f"{btn.TO_FAV}", ExecutorsFeed.show)
async def add_executor_to_favorites(message: Message, state: FSMContext, session: Any) -> None:
    """Лента исполнителей при нажатии кнопки избранное"""
    data = await state.get_data()
    client_tg_id = str(message.from_user.id)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем id клинета
    client_id: int = await AsyncOrm.get_client_id(client_tg_id, session)

    # Получаем текущего исполнителя
    executor: Executor = data["current_ex"]
    # Получаем всех исполнителей
    executors: list[Executor] = data["executors"]

    # Проверяем есть ли он уже в исполнителях
    already_in_fav: bool = await check_is_executor_in_favorites(client_tg_id, executor.id, session)
    if already_in_fav:
        await message.answer(f"{btn.INFO} Этот исполнитель уже есть у тебя в списке избранных")
        # return

    else:
        # Сохраняем исполнителя в избранное у клиента
        try:
            await AsyncOrm.add_executor_to_favorite(client_id, executor.id, session)
        except:
            await message.answer(f"Ошибка при добавлении исполнителя в избранное, попробуй позже")
            return

        await message.answer("Исполнитель сохранен в ⭐ избранное")

    is_last: bool = len(executors) == 1
    msg = executor_profile_to_show(executor, in_favorites=True)
    keyboard = kb.executor_show_keyboard(is_last)

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        # берем дефолтную, если нет фотографии пользователя
        filepath = settings.local_media_path + f"executor.jpg"
    try:
        profile_image = FSInputFile(filepath)

        await message.answer_photo(
            photo=profile_image,
            caption=msg,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")
        msg = f"Сервис временно недоступен, попробуй позже или обратись " \
              f"к администратору @{settings.admin_tg_username}"
        keyboard = to_main_menu()
        await message.answer(msg, reply_markup=keyboard.as_markup())


# НАПИСАТЬ ИСПОЛНИТЕЛЮ
@router.message(F.text == f"{btn.WRITE}", ExecutorsFeed.show)
async def connect_with_executor(message: Message, state: FSMContext, session: Any) -> None:
    """Связаться с исполнителем"""
    data = await state.get_data()
    client_tg_id = str(message.from_user.id)

    # Удаляем функциональные сообщения
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем текущего исполнителя
    executor: Executor = data["current_ex"]
    # Получаем username исполнителя для формирования ссылки
    username: str = await AsyncOrm.get_username(executor.tg_id, session)
    # Получаем id клиента по tg_id
    client_id: int = await AsyncOrm.get_client_id(client_tg_id, session)

    msg = ms.contact_with_executor(executor, username)
    keyboard = kb.contact_with_executor()

    functional_mess = await message.answer(msg, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)
    await state.update_data(functional_mess=functional_mess)

    # Сохраняем запись о просмотре контактов исполнителя
    await AsyncOrm.create_executor_view(executor.id, client_id, session)


# ОТМЕНА И ВОЗВРАЩЕНИЕ ИЗ РАЗНЫХ ТОЧЕК В ЛЕНТУ ИСПОЛНИТЕЛЕЙ
@router.callback_query(F.data == "cancel_executors_feed", StateFilter("*"))
async def back_to_executor_feed(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Для отмены различных callback"""
    data = await state.get_data()
    client_tg_id: str = str(callback.from_user.id)

    # Удаляем предыдущее сообщение
    try:
        await data["functional_mess"].delete()
    except:
        pass

    # Получаем текущего исполнителя
    executor: Executor = data["current_ex"]

    # Получаем исполнителей из памяти
    executors: list[Executor] = data["executors"]
    is_last: bool = len(executors) == 1

    already_in_fav = await check_is_executor_in_favorites(client_tg_id, executor.id, session)
    msg = executor_profile_to_show(executor, already_in_fav)
    keyboard = kb.executor_show_keyboard(is_last)

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        # берем дефолтную, если нет фотографии пользователя
        filepath = settings.local_media_path + f"executor.jpg"
    try:
        profile_image = FSInputFile(filepath)

        await callback.message.answer_photo(
            photo=profile_image,
            caption=msg,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")
        msg = f"Сервис временно недоступен, попробуй позже или обратись " \
              f"к администратору @{settings.admin_tg_username}"
        keyboard = to_main_menu()
        await callback.message.answer(msg, reply_markup=keyboard.as_markup())


async def check_is_executor_in_favorites(client_tg_id: str, executor_id: int, session: Any) -> bool:
    """Возвращает true если исполнитель в избранному, иначе false"""
    client_id: int = await AsyncOrm.get_client_id(client_tg_id, session)
    ex_in_favorites: bool = await AsyncOrm.executor_in_favorites(client_id, executor_id, session)
    return ex_in_favorites

