from typing import Any, List

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckPrivateMessageMiddleware
from routers.keyboards import admin as kb
from routers.buttons import buttons as btn
from routers.states.professions import AddProfession, AddJob
from schemas.profession import Profession, ProfessionAdd, Job, JobAdd

# Роутер для использования в ЛС
router = Router()
router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())
router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data.split("|")[1] == "admin_menu")
async def admin_menu(callback: CallbackQuery, session: Any) -> None:
    """Админ меню"""
    # Проверяем админ или нет
    tg_id = str(callback.from_user.id)
    is_admin: bool = await AsyncOrm.check_is_admin(tg_id, session)

    if not is_admin:
        keyboard = kb.back_to_main_menu_keyboard()
        await callback.answer()
        await callback.message.edit_text(f"{btn.INFO} Данный функционал доступен только для администраторов", reply_markup=keyboard.as_markup())
        return

    # Отправка сообщения
    keyboard = kb.admin_menu_keyboard()
    msg = f"{btn.ADMIN}"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


# ДОБАВЛЕНИЕ ПРОФЕССИИ
@router.callback_query(F.data == "add_profession")
async def add_profession_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало добавления профессии"""
    # Назначаем стейт
    await state.set_state(AddProfession.title)

    # Отправляем сообщение
    msg = "Отправьте название профессии"
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.cancel_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(AddProfession.title)
async def get_profession_title(message: Message, state: FSMContext, session: Any) -> None:
    """Получение названия профессии, запрос emoji"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text, disable_web_page_preview=True)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем есть ли уже такое название
    professions: List[Profession] = await AsyncOrm.get_professions(session)
    profession_titles: List[str] = [p.title for p in professions]
    if message.text in profession_titles:
        prev_mess = await message.answer(f"Название \"{message.text}\" уже существует, отправьте другое название",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем название
    await state.update_data(title=message.text)

    # Меняем стейт
    await state.set_state(AddProfession.emoji)

    # Отправляем сообщение
    msg = "Отправьте emoji для указанного названия"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(AddProfession.emoji)
async def get_profession_emoji(message: Message, state: FSMContext, session: Any) -> None:
    """Получение emoji, запрос подтверждения"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text, disable_web_page_preview=True)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем emoji
    await state.update_data(emoji=message.text)

    # Меняем стейт
    await state.set_state(AddProfession.confirmation)

    # Отправляем сообщение
    data = await state.get_data()
    msg = f"Добавить профессию <b>{data['emoji']} {data['title']}</b>?"
    prev_mess = await message.answer(msg, reply_markup=kb.yes_no_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "confirm", AddProfession.confirmation)
async def add_profession_confirmed(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Сохранение профессии"""
    # Получаем данные
    data = await state.get_data()

    # Скидываем стейт
    await state.clear()

    # Сохраняем профессию
    profession: ProfessionAdd = ProfessionAdd(
        title=data['title'],
        emoji=data['emoji'],
    )

    try:
        await AsyncOrm.create_profession(profession, session)
    except:
        await callback.answer()
        await callback.message.edit_text(f"{btn.INFO} Ошибка при сохранении профессии. Повторите запрос позже")
        return

    msg = f"✅ Профессия {profession.emoji} {profession.title} успешно добавлена"
    await callback.answer()
    await callback.message.edit_text(msg)
    await callback.message.answer(f"{btn.ADMIN}", reply_markup=kb.admin_menu_keyboard().as_markup())


# ДОБАВЛЕНИЕ JOB
@router.callback_query(F.data == "add_job")
async def add_job_start(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Начало добавления job"""
    # Назначаем стейт
    await state.set_state(AddJob.profession)

    # Получаем профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выберите профессию, в которую необходимо добавить раздел"
    await callback.answer()
    keyboard = kb.profession_keyboard(professions)
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", AddJob.profession)
async def get_profession(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получение профессии, запрос job title"""
    # Записываем profession_id
    profession_id = int(callback.data.split("|")[1])
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(AddJob.title)

    # Получаем данные для сообщения
    profession: Profession = await AsyncOrm.get_profession(profession_id, session)
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)
    jobs_text = "\n".join([job.title for job in jobs])
    await state.update_data(jobs=jobs)
    await state.update_data(profession=profession)

    # Запрашиваем title
    msg = f"Отправьте название раздела профессии\n\n"
    if jobs:
        msg += f"В профессии {profession.emoji + ' ' if profession.emoji else ''}{profession.title} уже имеются разделы:\n" \
               f"<i>{jobs_text}</i>"
    else:
        msg += f"В профессии {profession.emoji + ' ' if profession.emoji else ''}{profession.title} пока нет ни одного раздела"

    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.cancel_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(AddJob.title)
async def get_job_title(message: Message, state: FSMContext) -> None:
    """Получаем job title"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем есть ли уже такое название
    jobs: List[Job] = data["jobs"]
    jobs_titles: List[str] = [job.title for job in jobs]
    if message.text in jobs_titles:
        prev_mess = await message.answer(f"Название \"{message.text}\" уже существует, отправьте другое название",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем название
    await state.update_data(title=message.text)

    # Меняем стейт
    await state.set_state(AddJob.confirmation)

    # Отправляем сообщение
    msg = f"Добавить раздел <b>{message.text}</b> в профессию {data['profession'].emoji + ' ' if data['profession'].emoji else ''}{data['profession'].title}?"
    prev_mess = await message.answer(msg, reply_markup=kb.yes_no_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "confirm", AddJob.confirmation)
async def add_job_confirmed(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Сохранение job"""
    # Получаем данные
    data = await state.get_data()

    # Скидываем стейт
    await state.clear()

    # Сохраняем профессию
    job: JobAdd = JobAdd(
        title=data['title'],
        profession_id=data['profession_id'],
    )

    try:
        await AsyncOrm.create_job(job, session)
    except:
        await callback.answer()
        await callback.message.edit_text(f"{btn.INFO} Ошибка при сохранении раздела профессии. Повторите запрос позже")
        return

    msg = f"✅ Раздел {job.title} успешно добавлен в профессию {data['profession'].emoji + ' ' if data['profession'].emoji else ''}{data['profession'].title}"
    await callback.answer()
    await callback.message.edit_text(msg)
    await callback.message.answer(f"{btn.ADMIN}", reply_markup=kb.admin_menu_keyboard().as_markup())


@router.callback_query(F.data == "admin_cancel", StateFilter("*"))
async def cancel_admin_addition(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Отмена действия админа"""
    try:
        await state.clear()
    except Exception:
        pass

    await admin_menu(callback, session)






