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
from routers.states.professions import AddProfession
from schemas.profession import Profession, ProfessionAdd

# Роутер для использования в ЛС
router = Router()
router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())
router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data.split("|")[1] == "admin_menu")
async def admin_menu(callback: CallbackQuery, admin: bool) -> None:
    """Админ меню"""
    # Проверка админ ли
    if not admin:
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


@router.callback_query(F.data == "admin_cancel", StateFilter("*"))
async def cancel_registration(callback: CallbackQuery, state: FSMContext, admin: bool) -> None:
    """Отмена действия админа"""
    try:
        await state.clear()
    except Exception:
        pass

    await admin_menu(callback, admin)






