from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, CallbackQuery, Message

from database.orm import AsyncOrm
from routers.buttons import buttons as btn


class BanedMiddleware(BaseMiddleware):
    """
        Проверяет забанен ли пользователь в таблице Users БД
        Использовать после middleware с DB
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        # получаем сессию базы данных из контекста
        session: Any = data["session"]

        # проверяем есть ли бан у пользователя
        is_banned: bool = await self._check_user_is_banned(event, session)
        # user_already_has_role: bool = await self._check_user_has_role(event, session)

        if not is_banned:
            # для НЕ заблокированных пользователей
            return await handler(event, data)

        else:
            # отправляем сообщение о блокировке
            bot: Bot = data["bot"]
            return await send_banned_message(event, bot)

    async def _check_user_is_banned(self, event: TelegramObject, session: Any) -> bool:
        try:
            user_is_banned: bool = await AsyncOrm.user_is_banned(str(event.from_user.id), session)
            return user_is_banned
        except:
            return True     # в случае ошибок возвращаем True - пользователь в бане


async def send_banned_message(event: CallbackQuery | Message, bot: Bot) -> None:
    """Сообщение для заблокированных пользователей"""
    await bot.send_message(
        event.from_user.id,
        f"{btn.INFO} Вы не можете использовать данный сервис",
    )