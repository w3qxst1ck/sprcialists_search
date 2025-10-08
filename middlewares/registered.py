from collections.abc import Awaitable, Callable
from typing import Any
import asyncpg

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from settings import settings
from database.orm import AsyncOrm

from routers.start import show_unregistered_message


class RegisteredMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        conn = await asyncpg.connect(
            user=settings.db.postgres_user,
            host=settings.db.postgres_host,
            password=settings.db.postgres_password,
            port=settings.db.postgres_port,
            database=settings.db.postgres_db
        )

        # проверяем выбрал ли пользователь роль
        user_registered: bool = await self._check_is_user_registered(event, conn)

        if user_registered:
            # для зарегистрированных пользователей
            return await handler(event, data)

        else:
            # перенаправляем на регистрацию
            bot: Bot = data["bot"]
            return await show_unregistered_message(event, bot)

    async def _check_is_user_registered(self, event: TelegramObject, session: Any) -> bool:
        try:
            user_has_role: bool = await AsyncOrm.user_has_role(str(event.from_user.id), session)
            return user_has_role
        except Exception:
            return False
