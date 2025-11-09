import datetime
from typing import Any, List

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.executor_profile import executor_profile_menu
from routers.keyboards import edit_executor_profile as kb
from routers.keyboards.admin import confirm_edit_executor_keyboard
from routers.messages.executor import edited_executor_card_for_admin_verification
from routers.states.executor_profile import EditPhoto, EditExecutor

from schemas.executor import Executor

from logger import logger
from schemas.profession import Profession, Job
from schemas.user import User
from settings import settings
from utils.datetime_service import convert_date_and_time_to_str
from utils.download_files import load_photo_from_tg, get_photo_path
from utils.validations import is_valid_url

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


# ИЗМЕНЕНИЕ ФОТОГРАФИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "photo"))
async def edit_photo(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение фотографии"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditPhoto.photo)

    # Отправляем сообщение
    msg = "Отправь новое фото профиля"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditPhoto.photo)
async def get_photo(message: Message, bot: Bot, state: FSMContext) -> None:
    """Получение фото"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Проверяем что отправлено фото
    if not message.photo:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить фотографию",
                                         reply_markup=kb.cancel_edit_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем фото локально
    try:
        await load_photo_from_tg(message, bot, settings.executors_profile_path)
    except:
        msg = f"{btn.INFO} Ошибка при обновлении фото профиля. Повтори запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = f"✅ Фотография профиля успешно обновлена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
    tg_id = str(message.from_user.id)
    logger.info(f"Фото профиля исполнителя tg_id {tg_id} изменено")


# ИЗМЕНЕНИЕ ПРОФЕССИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "profession"), EditExecutor.view)
async def edit_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Изменение profession"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.profession)

    # Получаем доступные профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выбери профессию из списка"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.profession_keyboard(professions).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", EditExecutor.profession)
async def get_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Получение профессии, запрос Job"""
    profession_id = int(callback.data.split("|")[1])

    # Записываем профессию
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(EditExecutor.jobs)

    # Получаем Jobs для профессии
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Заготовка для мультиселекта
    selected_jobs = []

    # Записываем все Jobs и заготовку выбранных Jobs в стейт, чтобы каждый раз не получать заново
    await state.update_data(all_jobs=jobs)
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выбери категории (до 5 штук)"
    keyboard = kb.jobs_keyboard(jobs, selected_jobs)
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "choose_jobs", EditExecutor.jobs)
async def get_jobs_multiselect(callback: CallbackQuery, state: FSMContext) -> None:
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
            selected_jobs[0] = job_id
        else:
            selected_jobs.append(job_id)

    # Обновляем выбранные работы в стейте
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выбери категории (до 5 штук)"
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs)

    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "choose_jobs_done", EditExecutor.jobs)
async def get_jobs(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Запись Jobs после мультиселекта"""
    # Получаем дату
    data = await state.get_data()

    # Меняем стейт на view
    await state.set_state(EditExecutor.view)

    # Меняем профессии и jobs в БД
    jobs_ids = data["selected_jobs"]

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]

    profession: Profession = await AsyncOrm.get_profession(data["profession_id"], session)
    jobs: List[Job] = await AsyncOrm.get_jobs_by_ids(jobs_ids, session)
    executor.profession = profession
    executor.jobs = jobs
    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = f"✅ Профессии успешно изменены"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ЦЕНОВОЙ ИНФОРМАЦИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "rate"), EditExecutor.view)
async def edit_rate(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение ценовой информации"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.rate)

    # Отправляем сообщение
    msg = "Отправь текстом свою рабочую ставку (например: от 2000 ₽/час или 30 000 рублей/месяц)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.rate)
async def get_rate(message: Message, state: FSMContext) -> None:
    """Получаем ставку"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.rate = message.text

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Ценовая информация успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ОПЫТА
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "experience"), EditExecutor.view)
async def edit_experience(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение опыта"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.experience)

    # Отправляем сообщение
    msg = "Отправь информацию о своем рабочем опыте/уровень (например: 6 лет или senior)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.experience)
async def get_experience(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем опыт"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.experience = message.text

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Информация об опыте успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ОПИСАНИЯ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "description"), EditExecutor.view)
async def edit_description(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение описания"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.description)

    # Отправляем сообщение
    msg = "Отправь информацию о себе (не более 500 символов)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.description)
async def get_description(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем описание"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если текст длиннее 500 символов
    if len(message.text) > 500:
        prev_mess = await message.answer(
            f"Текст должен быть не более 500 символов, вы отправили {len(message.text)}",
            reply_markup=kb.cancel_edit_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.description = message.text

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Описание успешно изменено"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ КОНТАКТОВ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "contacts"), EditExecutor.view)
async def edit_contacts(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение контактов"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.contacts)

    # Отправляем сообщение
    msg = "Отправь контакты для связи (например телефон: 8-999-888-77-66)\n\n" \
          "❗<b>Важно</b>: указанные контакты будут видны другим пользователям сервиса"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.contacts)
async def get_contacts(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем контакты"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.skip_cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.contacts = message.text

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Контактная информация успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


@router.callback_query(F.data == "skip", EditExecutor.contacts)
async def skip_contacts(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись контактов пустыми"""
    data = await state.get_data()

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.contacts = None

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Контактная информация успешно изменена"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ГОРОД
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "location"), EditExecutor.view)
async def edit_location(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение location"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.location)

    # Отправляем сообщение
    msg = "Отправь свой город"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.location)
async def get_location(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем location"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.skip_cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.location = message.text

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Город успешно изменен"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


@router.callback_query(F.data == "skip", EditExecutor.location)
async def skip_location(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись location пустым"""
    data = await state.get_data()

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.location = None

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Город успешно изменен"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ССЫЛОК НА ПОРТФОЛИО
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "links"), EditExecutor.view)
async def edit_links(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение links"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExecutor.links)

    # Делаем заготовку под ссылки
    await state.update_data(links=[])

    # Отправляем сообщение
    msg = "Отдельными сообщениями отправь ссылки на портфолио"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExecutor.links)
async def get_link(message: Message, state: FSMContext) -> None:
    """Вспомогательный хэндлер для получения ссылок на портфолио"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text, disable_web_page_preview=True)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        # Проверяем может ли пользователь продолжить (если есть хотя бы одна валидная ссылка)
        if len(data["links"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_edit_keyboard()

        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если ссылка не валидна
    if not is_valid_url(message.text):
        # Проверяем может ли пользователь продолжить (если есть хотя бы одна валидная ссылка)
        if len(data["links"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_edit_keyboard()

        prev_mess = await message.answer("Неверный формат ссылки, необходимо отправить текст формата <i>https://www.google.com</i> "
                                         "без дополнительных символов\nОтправьте ссылку заново",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Записываем ссылку
    links = data["links"]
    links.append(message.text)
    links_text = "\n".join([f"{link}" for link in links])
    links_count = len(links)
    await state.update_data(links=links)

    # Отправляем сообщение
    msg = f"Отправь следующую ссылку или нажмите кнопку \"Продолжить\"\n\n" \
          f"Отправлено ссылок {links_count} шт.:\n{links_text}"
    prev_mess = await message.answer(msg, reply_markup=kb.continue_cancel_keyboard().as_markup(), disable_web_page_preview=True)

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "continue", EditExecutor.links)
async def get_links(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получаем список ссылок на портфолио, запрашиваем контакты"""
    # Получаем дату
    data = await state.get_data()

    # Меняем old_executor, если это первое изменение и нет new_executor
    if data.get("new_executor"):
        executor: Executor = data["new_executor"]
    else:
        executor: Executor = data["old_executor"]
    executor.links = data["links"]

    await state.update_data(new_executor=executor)

    # Отправляем сообщение
    msg = "✅ Ссылки на портфолио успешно изменены"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ОТПРАВКА ИЗМЕНЕННОЙ АНКЕТЫ НА ВЕРИФИКАЦИЮ
@router.callback_query(F.data.split("|")[0] == "send_to_verification", EditExecutor.view)
async def send_to_verification(callback: CallbackQuery, session: Any) -> None:
    """Подтверждение отправки анкеты на верификацию"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Получаем пользователя
    tg_id = str(callback.from_user.id)
    user: User = await AsyncOrm.get_user(tg_id, session)

    # Если пользователь существует и он хотя бы раз пытался зарегистрироваться
    ban_expired = (user.updated_at + datetime.timedelta(days=settings.registration_ban_days)) < datetime.datetime.now()
    if not ban_expired:
        # Высчитываем разрешенную дату
        allowed_date = user.updated_at + datetime.timedelta(days=settings.registration_ban_days)
        # Переводим в str
        allowed_date_text, allowed_time_text = convert_date_and_time_to_str(allowed_date, with_tz=True)
        msg = f"Изменение анкеты будет доступно после {allowed_date_text} {allowed_time_text} (МСК)"
        await callback.answer()
        await callback.message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    msg = f"❗ Во время проверки анкеты администратором большая часть функционала сервиса будет недоступна"
    keyboard = kb.send_to_verification_keyboard(tg_id)

    await callback.message.answer(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "send_to_verification_confirmed", EditExecutor.view)
async def send_to_verification_confirmed(callback: CallbackQuery, state: FSMContext, bot: Bot, session: Any) -> None:
    """Отправка анкеты на верификацию"""
    # Получаем данные
    tg_id = str(callback.from_user.id)
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохранение в БД обновленной анкеты с is_verified = False
    executor: Executor = data["new_executor"]
    executor.verified = False
    try:
        await AsyncOrm.update_executor(executor, session)
    except:
        await callback.answer()
        await callback.message.answer(f"{btn.INFO} Ошибка при изменении профиля, попробуйте позже")
        return

    # Сообщение исполнителю
    ex_msg = f"{btn.INFO} Анкета отправлена на проверку администратору\n\n"
    await callback.answer()
    await callback.message.edit_text(ex_msg)

    # Сообщение админам в группу
    admin_msg = edited_executor_card_for_admin_verification(executor)
    admin_group_id = settings.admin_group_id
    filepath = get_photo_path(settings.executors_profile_path, tg_id)
    profile_image = FSInputFile(filepath)
    await bot.send_photo(
        admin_group_id,
        photo=profile_image,
        caption=admin_msg,
        reply_markup=confirm_edit_executor_keyboard(tg_id).as_markup(),
    )


# ОТМЕНА ИЗМЕНЕНИЯ АНКЕТЫ
@router.callback_query(F.data == "cancel_edit_profile", StateFilter("*"))
async def cancel_edit_profile(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Отмена изменения профиля"""
    # await state.clear()

    try:
        await callback.answer()
        await callback.message.edit_text(callback.message.text)
    except Exception:
        pass

    await executor_profile_menu(callback, session, state)
