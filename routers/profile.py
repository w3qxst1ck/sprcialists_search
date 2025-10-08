from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.admin import AdminMiddleware
from middlewares.registered import RegisteredMiddleware
from routers.buttons import commands as cmd
from routers.keyboards.menu import main_menu_keyboard

from database.orm import AsyncOrm
from schemas.user import UserAdd
from database.tables import UserRoles

router = Router()
router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())
router.message.middleware.register(RegisteredMiddleware())


@router.callback_query(F.data.split("|")[1] == "test")
async def test_handler(callback: CallbackQuery):
    await callback.message.answer("Все норм вы зарегистрированы")


@router.message(Command(f"tester"))
async def start(message: types.Message) -> None:
    """Старт хендлер"""
    await message.answer("Middleware не использовался")
