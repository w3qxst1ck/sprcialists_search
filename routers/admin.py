from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckPrivateMessageMiddleware, CheckGroupMessageMiddleware


# Роутер для использования в группе
group_router = Router()
group_router.message.middleware.register(DatabaseMiddleware())
group_router.callback_query.middleware.register(DatabaseMiddleware())
group_router.message.middleware.register(AdminMiddleware())
group_router.callback_query.middleware.register(AdminMiddleware())
group_router.message.middleware.register(CheckGroupMessageMiddleware())
group_router.callback_query.middleware.register(CheckGroupMessageMiddleware())

# Роутер для использования в ЛС
private_router = Router()
private_router.message.middleware.register(DatabaseMiddleware())
private_router.callback_query.middleware.register(DatabaseMiddleware())
private_router.message.middleware.register(AdminMiddleware())
private_router.callback_query.middleware.register(AdminMiddleware())
private_router.message.middleware.register(CheckPrivateMessageMiddleware())
private_router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


@group_router.callback_query(F.data.split("|")[0] == "executor_confirm")
async def confirm_executor_registration(callback: CallbackQuery, session: Any, bot: Bot, admin: bool) -> None:
    """Верификация новой анкеты исполнителя в группе"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Убираем клавиатуру сразу после нажатия
    await callback.message.edit_reply_markup(reply_markup=None)

    # получаем tg_id исполнителя
    executor_tg_id = callback.data.split("|")[1]

    # Меняем статус верификации
    admin_tg_id = str(callback.from_user.id)
    await AsyncOrm.verify_executor(executor_tg_id, admin_tg_id, session)

    # Оповещаем админов в группе
    msg = f"✅ Анкета исполнителя верифицирована"
    await callback.message.reply(msg)

    # Оповещаем клиента
    msg = f"✅ Ваша анкета исполнителя верифицирована"
    await bot.send_message(
        executor_tg_id,
        msg
    )

