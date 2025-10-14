from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckPrivateMessageMiddleware, CheckGroupMessageMiddleware
from schemas.client import RejectReason
from routers.keyboards import admin as kb


# Роутер для использования в ЛС
private_router = Router()
private_router.message.middleware.register(DatabaseMiddleware())
private_router.callback_query.middleware.register(DatabaseMiddleware())
private_router.message.middleware.register(AdminMiddleware())
private_router.callback_query.middleware.register(AdminMiddleware())
private_router.message.middleware.register(CheckPrivateMessageMiddleware())
private_router.callback_query.middleware.register(CheckPrivateMessageMiddleware())









