from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery, BufferedInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware

from database.orm import AsyncOrm

from routers.buttons import commands as cmd
from routers.keyboards import main_menu as kb

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())


@router.callback_query(F.data == "main_menu")
@router.message(Command(cmd.MENU[0]))
async def main_menu(message: CallbackQuery | Message, session: Any):
    """Главное меню"""
    tg_id = str(message.from_user.id)

    # Получаем роль пользователя
    user_role = await AsyncOrm.get_user_role(tg_id, session)

    msg = f"Главное меню {user_role}"
    keyboard = kb.main_menu(user_role)

    if isinstance(message, Message):
        await message.answer(msg, reply_markup=keyboard.as_markup())
    else:
        await message.message.answer(msg, reply_markup=keyboard.as_markup())




