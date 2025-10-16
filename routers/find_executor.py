from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_executor as kb
from routers.messages.executor import executor_profile_to_show
from routers.states.find import SelectJobs, ExecutorsFeed
from routers.buttons import buttons as btn
from schemas.profession import Profession, Job
from schemas.executor import ExecutorShow
from utils.shuffle import shuffle_executors

from settings import settings
from logger import logger

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

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

    msg = "Выберите рубрику"
    keyboard = kb.professions_keyboard(professions)

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

    msg = f"Выберите подкатегории для поиска"
    keyboard = kb.jobs_keyboard(jobs, selected)

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
        selected.append(selected_job_id)

    msg = f"Выберите подкатегории для поиска"
    keyboard = kb.jobs_keyboard(jobs, selected)

    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Обновляем данные с выбранными jobs
    await state.update_data(selected=selected)
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "find_ex_show|show_executors", SelectJobs.jobs)
async def end_multiselect(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Завершение мультиселекта и подбор подходящих исполнителей"""
    # Отправляем сообщение об ожидании
    wait_mess = await callback.message.edit_text(btn.WAIT_MSG)

    # Получаем все данные
    data = await state.get_data()
    jobs_ids: list[int] = data["selected"]

    # Получаем список подходящих исполнителей
    executors: list[ExecutorShow] = await AsyncOrm.get_executors_by_jobs(jobs_ids, session)

    # Если исполнителей нет
    if not executors:
        # Очищаем стейт
        await state.clear()
        await wait_mess.message.edit_text("Исполнителей по вашему запросу не найдено")
        return

    # Удаляем сообщение об ожидании
    try:
        await wait_mess.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(ExecutorsFeed.show)

    # Сортируем список в случайный порядок
    shuffled_executors: list[ExecutorShow] = shuffle_executors(executors)

    # Получаем первого исполнителя
    executor = shuffled_executors.pop()

    # Остальных исполнителей сохраняем в память
    await state.update_data(executors=shuffled_executors)

    # Выводим первого исполнителя
    msg = executor_profile_to_show(executor)
    keyboard = kb.executor_show_keyboard()

    # Получаем фото
    if executor.photo:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    else:
        filepath = settings.local_media_path + settings.executors_profile_path + f"{executor.tg_id}.jpg"
    try:
        profile_image = FSInputFile(filepath)
    except Exception as e:
        logger.error(f"Ошибка при загрузке фото исполнителя {filepath} {executor.tg_id}: {e}")

    await callback.message.answer(msg, reply_markup=keyboard, disable_web_page_preview=True)

    await callback.message.answer_photo(
        photo=profile_image,
        caption=msg,
        reply_markup=keyboard,
    )






