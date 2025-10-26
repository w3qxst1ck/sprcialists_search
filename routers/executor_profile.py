import os
from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import buttons as btn
from routers.buttons.buttons import WAIT_MSG
from routers.keyboards import executor_profile as kb
from routers.keyboards.client_reg import to_main_menu
from routers.menu import main_menu
from routers.messages.executor import get_executor_profile_message
from routers.states.registration import UploadCV

from schemas.executor import Executor

from logger import logger
from settings import settings
from utils.download_files import get_photo_path, get_cv_path, check_cv_file, load_photo_from_tg, load_cv_from_tg

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


# МЕНЮ ПРОФИЛЯ ИСПОЛНИТЕЛЯ
@router.callback_query(F.data.split("|")[1] == "executor_profile")
async def executor_profile_menu(callback: CallbackQuery, session: Any) -> None:
    """Меню профиля исполнителя"""
    # Wait message со случаем возвращения от файла
    try:
        await callback.answer()
        wait_msg = await callback.message.edit_text(WAIT_MSG)
    except:
        try:
            await callback.message.edit_reply_markup()
            wait_msg = await callback.message.answer(WAIT_MSG)
        except:
            wait_msg = await callback.message.answer(WAIT_MSG)

    # Получаем исполнителя
    tg_id = str(callback.from_user.id)
    executor: Executor | None = await AsyncOrm.get_executor_by_tg_id(tg_id, session)
    if not executor:
        msg = f"{btn.INFO} Ошибка при получении профиля, повторите попытку позже"
        await wait_msg.edit_text(msg)
        return

    # Формируем анкету
    questionnaire = get_executor_profile_message(executor)

    # Добавляем кнопки для редактирования анкеты
    buttons_text = f"\n\n<i>Нажмите на соответствующую цифру для редактирования анкеты:</i>\n" \
                   f"<b>1.</b> Изменить фотографию\n" \
                   f"<b>2.</b> Изменить профессию\n" \
                   f"<b>3.</b> Изменить ценовую информацию\n" \
                   f"<b>4.</b> Изменить информацию об опыте\n" \
                   f"<b>5.</b> Изменить информацию о себе\n" \
                   f"<b>6.</b> Изменить контактную информацию\n" \
                   f"<b>7.</b> Изменить город\n" \
                   f"<b>8.</b> Изменить ссылки на портфолио"

    caption = questionnaire + buttons_text

    # Получаем фотографию
    filepath = get_photo_path(settings.executors_profile_path, executor.tg_id)
    profile_image = FSInputFile(filepath)

    # Проверяем есть ли резюме
    cv_exists: bool = check_cv_file(executor.tg_id)

    # Удаляем сообщения ожидания
    try:
        await wait_msg.delete()
    except Exception:
        pass

    # Отправляем сообщение
    keyboard = kb.executor_profile_keyboard(cv_exists=cv_exists)
    await callback.message.answer_photo(
        profile_image,
        caption=caption,
        reply_markup=keyboard.as_markup()
    )


# ЗАГРУЗКА РЕЗЮМЕ
@router.callback_query(F.data == "upload_cv")
async def upload_resume_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало загрузки резюме"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(UploadCV.cv)

    msg = "Отправьте резюме <b>одним фалом</b>, допускается только формат <b>.pdf</b>"

    # Отправляем сообщение
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_upload_cv_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(UploadCV.cv)
async def get_cv_file(message: Message, state: FSMContext, bot: Bot) -> None:
    """Получение файла резюме"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except Exception:
        pass

    # Если отправлен не файл
    if not message.document:
        prev_mess = await message.answer("Неверный формат данных. Необходимо отправить файл расширения <b>.pdf</b>",
                                         reply_markup=kb.cancel_upload_cv_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем что файл расширения pdf
    if message.document.file_name[-4:] != ".pdf":
        prev_mess = await message.answer("Неверный формат данных. Необходимо отправить файл расширения <b>.pdf</b>",
                                         reply_markup=kb.cancel_upload_cv_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем файл
    try:
        await load_cv_from_tg(message, bot, settings.executors_cv_path)
    except:
        msg = f"{btn.INFO} Ошибка при загрузке файла, повторите попытку позже"
        await message.answer(msg, reply_markup=kb.to_executor_profile_keyboard().as_markup())
        return

    # Очищаем стейт
    await state.clear()

    # Отправляем сообщение
    msg = "✅ Файл резюме добавлен"
    await message.answer(msg, reply_markup=kb.to_executor_profile_keyboard().as_markup())


# ПРОСМОТР РЕЗЮМЕ
@router.callback_query(F.data == "download_cv")
async def download_cv(callback: CallbackQuery) -> None:
    """Скачивание своего резюме"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Получаем резюме
    tg_id = str(callback.from_user.id)
    filepath = get_cv_path(settings.executors_cv_path, tg_id)
    cv = FSInputFile(filepath)

    # Отправляем файл
    await callback.message.answer_document(cv, reply_markup=kb.back_from_cv_file_keyboard().as_markup())


# УДАЛЕНИЕ РЕЗЮМЕ
@router.callback_query(F.data == "delete_cv")
async def delete_cv(callback: CallbackQuery) -> None:
    """Удаление резюме"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Удаление файла
    tg_id = str(callback.from_user.id)
    filepath = get_cv_path(settings.executors_cv_path, tg_id)
    try:
        os.remove(filepath)
    except:
        msg = f"{btn.INFO} Ошибка при удалении файла. Повторите запрос позже"
        await callback.message.answer(msg, reply_markup=kb.back_from_cv_file_keyboard().as_markup())
        return

    # Отправляем сообщение
    msg = f"✅ Файл резюме успешно удален"
    await callback.message.answer(msg, reply_markup=kb.back_from_cv_file_keyboard().as_markup())


# ОТМЕНА ЗАГРУЗКИ РЕЗЮМЕ
@router.callback_query(F.data == "cancel_upload_cv", StateFilter("*"))
async def cancel_upload_cv(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Отмена загрузки резюме"""
    await state.clear()

    try:
        await callback.answer()
        await callback.message.edit_text(callback.message.text)
    except Exception:
        pass

    await executor_profile_menu(callback, session)