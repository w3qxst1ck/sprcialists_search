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


# from database.database import async_engine
# from database.tables import Base


async def set_commands(bot: io.Bot):
    """Перечень команд для бота"""
    commands = [
        BotCommand(command=f"start", description=f"🚀 Запуск"),
    ]

    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def set_description(bot: io.Bot):
    """Описание бота до запуска"""
    await bot.set_my_description(
         f"Сервис, который помогает фрилансерам находить клиентов.\n\n"
         f"- Быстро\n- Удобно\n- Просто\n\n Ежедневно отправляются тысячи заявок профессионалам,"
         f"экономя время на поиски вакансий.\n\n- Гарантируем качество\n— Заботимся о пользователях\n\n"
         f"Жмите /start, и начни получать заказы прямо сейчас\n\nОтзывы: @{settings.admin_tg_username}"
    )


async def start_bot() -> None:
    """Запуск бота"""
    bot = io.Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await set_commands(bot)
    await set_description(bot)

    storage = MemoryStorage()
    dp = io.Dispatcher(storage=storage)

    # ROUTERS
    dp.include_router(main_router)

    # MIDDLEWARES
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    # dp.message.middleware(AdminMiddleware())
    # dp.callback_query.middleware(AdminMiddleware())

    # TODO create tables DEV
    await AsyncOrm.create_tables()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
