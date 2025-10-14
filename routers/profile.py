from typing import Any

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

from database.tables import UserRoles
from database.orm import  AsyncOrm
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware

from routers.messages.client import get_client_profile_message
from routers.keyboards import profile as kb
from schemas.client import Client

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())


@router.callback_query(F.data == "main_menu|my_profile")
async def profile_handler(callback: CallbackQuery, session: Any):
    """Хэндлер для работы с профилем"""
    tg_id = str(callback.from_user.id)
    # Определяем роль
    user_role = await AsyncOrm.get_user_role(tg_id, session)

    if user_role == UserRoles.CLIENT.value:
        # Получаем клиента
        client: Client = await AsyncOrm.get_client(tg_id, session)

        # Формируем сообщение
        msg = get_client_profile_message(client)
        keyboard = kb.profile_menu()

        await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


