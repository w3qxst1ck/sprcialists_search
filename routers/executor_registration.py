from aiogram import Router, types, F, Bot
from aiogram.filters import Command, and_f
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.admin import AdminMiddleware
from routers.buttons import commands as cmd
from routers.keyboards.menu import main_menu_keyboard

from database.orm import AsyncOrm
from schemas.user import UserAdd
from database.tables import UserRoles


router = Router()
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())


@router.callback_query(and_f(F.data.split("|")[0] == "choose_role", F.data.split("|")[1] == "executor"))
async def start(message: types.Message, admin: bool, session: any) -> None:
    """Начало регистрации исполнителя"""
    pass
