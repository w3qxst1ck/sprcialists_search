from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.orm import AsyncOrm


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


async def send_empty_role_message(event: CallbackQuery | Message, bot: Bot) -> None:
    """Сообщение для пользователей не выбравших роль"""
    keyboard = await choose_role_keyboard()
    await bot.send_message(
        event.from_user.id,
        "Чтобы получить доступ к функциям бота, вам необходимо создать профиль\"клиента\" или \"исполнителя\"",
        reply_markup=keyboard.as_markup()
    )


async def choose_role_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура выбора роли"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Я клиент", callback_data="choose_role|client"))
    keyboard.row(InlineKeyboardButton(text=f"Я исполнитель", callback_data="choose_role|executor"))

    return keyboard