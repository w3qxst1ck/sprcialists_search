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
from settings import settings

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@router.message(Command(cmd.INSTRUCTION[0]))
async def instruction(message: Message):
    """Инструкция"""
    await message.answer("Инструкция")


@router.message(Command(cmd.HELP[0]))
async def help(message: Message):
    """Помощь"""
    await message.answer(f"Свяжитесь с администратором @{settings.admin_tg_username}")