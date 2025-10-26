from typing import Any, List

from aiogram import Router, F, Bot
from aiogram.filters import or_f, StateFilter, and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.buttons.buttons import WAIT_MSG
from routers.executor_profile import executor_profile_menu
from routers.keyboards import edit_executor_profile as kb
from routers.states.executor_profile import EditPhoto, EditProfession, EditRate, EditExperience, EditDescription, \
    EditContacts, EditLocation, EditLinks

from schemas.executor import Executor

from logger import logger
from schemas.profession import Profession, Job
from settings import settings
from utils.download_files import load_photo_from_tg
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
    msg = "Отправьте новое фото профиля"
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
        msg = f"{btn.INFO} Ошибка при обновлении фото профиля. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = f"✅ Фотография профиля успешно обновлена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
    tg_id = str(message.from_user.id)
    logger.info(f"Фото профиля исполнителя tg_id {tg_id} изменено")


# ИЗМЕНЕНИЕ ПРОФЕССИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "profession"))
async def edit_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Изменение profession"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditProfession.profession)

    # Получаем доступные профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выберите профессию из списка"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.profession_keyboard(professions).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", EditProfession.profession)
async def get_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Получение профессии, запрос Job"""
    profession_id = int(callback.data.split("|")[1])

    # Записываем профессию
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(EditProfession.jobs)

    # Получаем Jobs для профессии
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Заготовка для мультиселекта
    selected_jobs = []

    # Записываем все Jobs и заготовку выбранных Jobs в стейт, чтобы каждый раз не получать заново
    await state.update_data(all_jobs=jobs)
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выберите специализации из списка (до 5 штук)"
    keyboard = kb.jobs_keyboard(jobs, selected_jobs)
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "choose_jobs", EditProfession.jobs)
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
    msg = "Выберите специализации из списка (до 5 штук)"
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs)
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "choose_jobs_done", EditProfession.jobs)
async def get_jobs(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Запись Jobs после мультиселекта"""
    # Получаем дату
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Меняем профессии и jobs в БД
    tg_id = str(callback.from_user.id)
    jobs_ids = data["selected_jobs"]
    try:
        await AsyncOrm.update_profession(tg_id, jobs_ids, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении профессий. Повторите запрос позже"
        await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = f"✅ Профессии успешно изменены"
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ЦЕНОВОЙ ИНФОРМАЦИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "rate"))
async def edit_rate(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение ценовой информации"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditRate.rate)

    # Отправляем сообщение
    msg = "Отправьте текстом вашу рабочую ставку (например: от 2000 ₽/час или 30 000 рублей/месяц)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditRate.rate)
async def get_rate(message: Message, state: FSMContext, session: Any) -> None:
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

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(message.from_user.id)
        await AsyncOrm.update_rate(tg_id, message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении ценовой информации. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Ценовая информация успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ОПЫТА
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "experience"))
async def edit_experience(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение опыта"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditExperience.experience)

    # Отправляем сообщение
    msg = "Отправьте информацию о своем рабочем опыте/уровень (например: 6 лет или senior)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditExperience.experience)
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

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(message.from_user.id)
        await AsyncOrm.update_experience(tg_id, message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении информации об опыте. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Информация об опыте успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ОПИСАНИЯ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "description"))
async def edit_description(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение описания"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditDescription.description)

    # Отправляем сообщение
    msg = "Отправьте информацию о себе (не более 500 символов)"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditDescription.description)
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

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(message.from_user.id)
        await AsyncOrm.update_description(tg_id, message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении описания. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Описание успешно изменено"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ КОНТАКТОВ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "contacts"))
async def edit_contacts(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение контактов"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditContacts.contacts)

    # Отправляем сообщение
    msg = "Отправьте контакт для связи (например телефон: 8-999-888-77-66)\n\n" \
          "❗<b>Важно</b>: указанные контакты будут видны другим пользователям сервиса"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditContacts.contacts)
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

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(message.from_user.id)
        await AsyncOrm.update_contacts(tg_id, message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении контактной информации. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Контактная информация успешно изменена"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


@router.callback_query(F.data == "skip", EditContacts.contacts)
async def skip_contacts(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись контактов пустыми"""
    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(callback.from_user.id)
        await AsyncOrm.update_contacts(tg_id, None, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении контактной информации. Повторите запрос позже"
        await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Контактная информация успешно изменена"
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ГОРОД
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "location"))
async def edit_location(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение location"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditLocation.location)

    # Отправляем сообщение
    msg = "Отправьте ваш город"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditLocation.location)
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

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(message.from_user.id)
        await AsyncOrm.update_location(tg_id, message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении города. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Город успешно изменен"
    await message.answer(msg, reply_markup=kb.to_profile_keyboard().as_markup())


@router.callback_query(F.data == "skip", EditLocation.location)
async def skip_location(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись location пустым"""
    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(callback.from_user.id)
        await AsyncOrm.update_location(tg_id, None, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении города. Повторите запрос позже"
        await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Город успешно изменен"
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ИЗМЕНЕНИЕ ССЫЛОК НА ПОРТФОЛИО
@router.callback_query(and_f(F.data.split("|")[0] == "edit_executor", F.data.split("|")[1] == "links"))
async def edit_links(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение links"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditLinks.links)

    # Делаем заготовку под ссылки
    await state.update_data(links=[])

    # Отправляем сообщение
    msg = "Отдельными сообщениями отправьте ссылки на портфолио"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditLinks.links)
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
    msg = f"Отправьте следующую ссылку или нажмите кнопку \"Продолжить\"\n\n" \
          f"Отправлено ссылок {links_count} шт.:\n{links_text}"
    prev_mess = await message.answer(msg, reply_markup=kb.continue_cancel_keyboard().as_markup(), disable_web_page_preview=True)

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "continue", EditLinks.links)
async def get_links(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получаем список ссылок на портфолио, запрашиваем контакты"""
    # Получаем дату
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        tg_id = str(callback.from_user.id)
        links = data["links"]
        await AsyncOrm.update_links(tg_id, links, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении ссылок на портфолио. Повторите запрос позже"
        await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Ссылки на портфолио успешно изменены"
    await callback.message.edit_text(msg, reply_markup=kb.to_profile_keyboard().as_markup())


# ОТМЕНА ИЗМЕНЕНИЯ АНКЕТЫ
@router.callback_query(F.data == "cancel_edit_profile", StateFilter("*"))
async def cancel_upload_cv(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Отмена изменения профиля"""
    await state.clear()

    try:
        await callback.message.edit_text(callback.message.text)
    except Exception:
        pass

    await executor_profile_menu(callback, session)
