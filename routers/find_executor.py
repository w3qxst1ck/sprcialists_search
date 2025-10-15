from typing import Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.keyboards import find_executor as kb
from routers.states.find import SelectJobs
from routers.buttons import buttons as btn
from schemas.profession import Profession, Job

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
    await state.update_data(jobs=jobs, selected=[])

    msg = f"Выберите подкатегории для поиска"
    keyboard = kb.jobs_keyboard(jobs, selected=[])

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

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "find_ex_show|show_executors", SelectJobs.jobs)
async def end_multiselect(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершение мультиселекта и подбор подходящих исполнителей"""
    # Отправляем сообщение об ожидании
    wait_mess = await callback.message.edit_text(btn.WAIT_MSG)

    # Получаем все данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # executors = await AsyncOrm.

    await callback.message.edit_text(f"Выбранные id: {data['selected']}")



