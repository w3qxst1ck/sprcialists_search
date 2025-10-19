from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, ReplyKeyboardRemove

from database.tables import UserRoles
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware

from database.orm import AsyncOrm

from routers.buttons import commands as cmd, buttons as btn
from routers.keyboards import menu as kb
from routers.messages import menu as ms
from logger import logger

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.callback_query(F.data == "main_menu")
@router.message(Command(cmd.MENU[0]))
async def main_menu(message: CallbackQuery | Message, session: Any, state: FSMContext = None):
    """Главное меню"""
    # Убираем клавиатуру, если она была до этого
    try:
        if isinstance(message, Message):
            wait_mess = await message.answer(f"{btn.WAIT_MSG}", reply_markup=ReplyKeyboardRemove())
        else:
            wait_mess = await message.message.answer(f"{btn.WAIT_MSG}", reply_markup=ReplyKeyboardRemove())
        await wait_mess.delete()
    except:
        pass

    # Скидываем стейт если пришли по кнопке назад
    if state:
        try:
            await state.clear()
        except Exception:
            pass

    tg_id = str(message.from_user.id)

    # Получаем роль пользователя
    user_role: str = await AsyncOrm.get_user_role(tg_id, session)

    # Проверяем верификацию (только для исполнителей)
    if user_role == UserRoles.EXECUTOR.value:
        is_verified = await AsyncOrm.is_verified(tg_id, session)
        # Если исполнитель не верифицирован
        if not is_verified:
            msg = "Данные функционал доступен только верифицированным пользователям"
            if isinstance(message, Message):
                await message.answer(msg)
            else:
                await message.message.edit_text(msg)
            return

    # Формируем сообщение
    msg = ms.get_menu_message(user_role)
    keyboard = kb.main_menu(user_role)

    # Загружаем картину для главного меню
    try:
        # menu_image = FSInputFile(settings.local_media_path + "menu.jpg")
        if isinstance(message, Message):
            # await message.answer_photo(photo=menu_image, caption=msg, reply_markup=keyboard.as_markup())
            await message.answer(msg, reply_markup=keyboard.as_markup())
        else:
            try:
                # await message.message.answer_photo(photo=menu_image, caption=msg, reply_markup=keyboard.as_markup())
                await message.message.edit_text(msg, reply_markup=keyboard.as_markup())
            # В случаем если не получилось отредактировать callback (например он был с фото), просто отвечаем
            except:
                await message.message.answer(msg, reply_markup=keyboard.as_markup())

    except Exception as e:
        logger.error(f"Не удалось загрузить картинку главного меню: {e}")



