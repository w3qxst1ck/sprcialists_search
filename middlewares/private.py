from collections.abc import Awaitable, Callable
from typing import Any, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class CheckPrivateMessageMiddleware(BaseMiddleware):
    """Проверка сообщения в лс, а не группу"""
    async def __call__(self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:

        # типа чата
        if data["event_chat"].type == "private":
            return await handler(event, data)
        return


class CheckGroupMessageMiddleware(BaseMiddleware):
    """Проверка сообщения в лс, а не группу"""
    async def __call__(self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:

        # типа чата
        if data["event_chat"].type == "group":
            return await handler(event, data)
        return