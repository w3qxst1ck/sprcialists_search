from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.filters import Command, and_f, StateFilter
from aiogram.fsm.context import FSMContext

from middlewares.database import DatabaseMiddleware
from routers.states.registration import Executor

from middlewares.admin import AdminMiddleware
from routers.buttons import commands as cmd
from routers.keyboards.menu import main_menu_keyboard

from database.orm import AsyncOrm
from schemas.profession import Job, Profession
from schemas.user import UserAdd
from database.tables import UserRoles
from settings import settings
from routers.keyboards import executor_registration as kb
from utils.validations import is_valid_age

router = Router()
router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())


@router.callback_query(and_f(F.data.split("|")[0] == "choose_role", F.data.split("|")[1] == "executor"))
async def start_registration(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Начало регистрации исполнителя"""
    # Проверка уже выбранной роли у пользователя
    tg_id = str(callback.from_user.id)
    role: str | None = await AsyncOrm.get_user_role(tg_id, session)
    if role:
        role_text = settings.roles[role]
        msg = f"У вас уже выбрана роль {role_text}"
        await callback.message.edit_text(msg)
        return

    # Ставим стейт
    await state.set_state(Executor.name)

    # Отправляем сообщение
    msg = "Отправьте Имя/ник, который будут видеть клиенты"
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.name)
async def get_name(message: types.Message, session: Any, state: FSMContext) -> None:
    """Запись имени, запрос возраста"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст")
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем имя
    await state.update_data(name=message.text)

    # Меняем стейт
    await state.set_state(Executor.age)

    # Отправляем сообщение с запросом возраста
    msg = "Укажите возраст"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.age)
async def get_age(message: types.Message, session: Any, state: FSMContext) -> None:
    """Получение возраста, запрос профессии"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст", reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если возраст введен некорректный
    if not is_valid_age(message.text):
        prev_mess = await message.answer("Необходимо отправить возраст одним числом от 18 до 100", reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем возраст
    await state.update_data(age=int(message.text))

    # Меняем стейт
    await state.set_state(Executor.profession)

    # Получаем доступные профессии
    # TODO получать из базы
    professions = [
        Profession(id=1, title="Designer"),
        Profession(id=2, title="Developer"),
        Profession(id=3, title="VideoMaker"),
    ]

    # Отправляем сообщение
    msg = "Выберите профессию из списка"
    prev_mess = await message.answer(msg, reply_markup=kb.profession_keyboard(professions).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", Executor.profession)
async def get_profession(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Получение профессии, запрос Job"""
    profession_id = int(callback.data.split("|")[1])

    # Записываем профессию
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(Executor.jobs)

    # Получаем Jobs для профессии
    # TODO брать из базы
    all_jobs = [
        Job(id=1, title="Веб разработка"),
        Job(id=2, title="Frontend"),
        Job(id=3, title="Backend"),
        Job(id=4, title="Devops"),
        Job(id=5, title="1C"),
        Job(id=6, title="CloudDev"),
    ]

    # Заготовка для мультиселекта
    selected_jobs = []

    # Записываем все Jobs и заготовку выбранных Jobs в стейт, чтобы каждый раз не получать заново
    await state.update_data(all_jobs=all_jobs)
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выберите специализации из списка (до 5 штук)"
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs)
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "choose_jobs", Executor.jobs)
async def get_jobs_multiselect(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Вспомогательный хендлер для мультиселекта"""
    job_id = int(callback.data.split("|")[1])

    # Получаем данные из стейта
    data = await state.get_data()
    selected_jobs = data["selected_jobs"]
    all_jobs = data["all_jobs"]

    # Добавляем или удаляем Job из списка выбранных
    if job_id in selected_jobs:
        selected_jobs.remove(job_id)
    else:
        # Убираем одну если больше 5
        if len(selected_jobs) == 5:
            selected_jobs.pop()

        selected_jobs.append(job_id)

    # Обновляем выбранные работы в стейте
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выберите специализации из списка (до 5 штук)"
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs)
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "choose_jobs_done", Executor.jobs)
async def get_jobs(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись Jobs после мультиселекта, запрос описания"""
    data = await state.get_data()
    jobs = ", ".join(data["selected_jobs"])
    await callback.message.edit_text(jobs)


@router.callback_query(F.data == "cancel_executor_registration", StateFilter("*"))
async def cancel_registration(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Отмена регистрации"""
    await state.clear()
    msg = f"Нажмите /{cmd.START[0]}, чтобы начать регистрацию заново"
    await callback.message.edit_text(msg)

