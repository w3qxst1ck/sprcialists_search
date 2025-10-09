from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject
from database.orm import AsyncOrm

from routers.start import send_empty_role_message


class RegisteredMiddleware(BaseMiddleware):
    """
        Проверяет определена уже роль у пользователя или нет.
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

        # проверяем выбрал ли пользователь роль
        user_already_has_role: bool = await self._check_user_has_role(event, session)

        if user_already_has_role:
            # для зарегистрированных пользователей
            return await handler(event, data)

        else:
            # перенаправляем на регистрацию
            bot: Bot = data["bot"]
            return await send_empty_role_message(event, bot)

    async def _check_user_has_role(self, event: TelegramObject, session: Any) -> bool:
        try:
            user_has_role: bool = await AsyncOrm.user_has_role(str(event.from_user.id), session)
            return user_has_role
        except Exception:
            return False


