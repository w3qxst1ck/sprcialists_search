import asyncio
from datetime import datetime
from database.orm import AsyncOrm

import aiogram as io
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from settings import settings
from routers import main_router
from routers.buttons import commands as cmd


# from database.database import async_engine
# from database.tables import Base


async def set_commands(bot: io.Bot):
    """Перечень команд для бота"""
    commands = [
        BotCommand(command=f"{cmd.MENU[0]}", description=f"{cmd.MENU[1]}"),
        BotCommand(command=f"{cmd.START[0]}", description=f"{cmd.START[1]}"),
        # BotCommand(command=f"{cmd.INSTRUCTION[0]}", description=f"{cmd.INSTRUCTION[1]}"),
        # BotCommand(command=f"{cmd.HELP[0]}", description=f"{cmd.HELP[1]}")
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def set_description(bot: io.Bot):
    """Описание бота до запуска"""
    await bot.set_my_description(
         f"👋 Привет, это PRUV — бот для быстрого поиска креативных специалистов.\n\n"
         f"Мы собрали <b>проверенных исполнителей</b> по разным креативным направлениям:\n\n"
         f"✔️ Дизайн\n✔️️ Фото\n✔️ Видео\n✔️ SMM\n\n"
         f"🔍 Заказчики могут быстро найти исполнителя под нужную задачу. А исполнители – новые заказы.\n\n"
         f"<b>Все анкеты исполнителей проходят ручную модерацию, поэтому твой проект в надежных руках!</b>\n\n"
         f"👇 Нажми Start, чтобы выбрать роль и начать работу.",
    )


async def start_bot() -> None:
    """Запуск бота"""
    bot = io.Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await set_commands(bot)
    # await set_description(bot)

    storage = MemoryStorage()
    dp = io.Dispatcher(storage=storage)

    # ROUTERS
    dp.include_router(main_router)

    # MIDDLEWARES
    # dp.message.middleware(DatabaseMiddleware())
    # dp.callback_query.middleware(DatabaseMiddleware())
    # dp.message.middleware(AdminMiddleware())
    # dp.callback_query.middleware(AdminMiddleware())

    # TODO create tables DEV
    # await AsyncOrm.create_tables()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
