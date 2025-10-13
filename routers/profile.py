from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())


@router.callback_query(F.data.split("|")[1] == "test")
async def test_handler(callback: CallbackQuery):
    await callback.message.answer("Все норм вы зарегистрированы")

