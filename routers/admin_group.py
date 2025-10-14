from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckPrivateMessageMiddleware, CheckGroupMessageMiddleware
from schemas.executor import RejectReason
from routers.keyboards import admin as kb

# Роутер для использования в группе
group_router = Router()
group_router.message.middleware.register(DatabaseMiddleware())
group_router.callback_query.middleware.register(DatabaseMiddleware())
group_router.message.middleware.register(AdminMiddleware())
group_router.callback_query.middleware.register(AdminMiddleware())
group_router.message.middleware.register(CheckGroupMessageMiddleware())
group_router.callback_query.middleware.register(CheckGroupMessageMiddleware())


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
    admin_name = str(callback.from_user.first_name)
    msg = f"\n\n✅ <i>Анкета верифицирована администратором \"{admin_name}\"</i>"
    await callback.message.edit_caption(caption=callback.message.caption + msg)

    # Оповещаем исполнителя
    msg = f"✅ Ваша анкета успешно верифицирована\n\nТеперь вашу анкету будут видеть клиенты/заказчики"
    await bot.send_message(executor_tg_id, msg)


# Отказ в верификации исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_cancel")
async def cancel_executor_verification(callback: CallbackQuery, session: Any, admin: bool) -> None:
    """Выбор причины отказа в верификации профиля исполнителя"""
    # Убираем клавиатуру сразу после нажатия
    await callback.message.edit_reply_markup(reply_markup=None)

    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Получаем tg_id исполнителя
    user_tg_id = callback.data.split("|")[1]

    reject_reasons: list[RejectReason] = await AsyncOrm.get_reject_reasons(session)

    msg = "Выберите причину отказа регистрации"
    keyboard = kb.all_reasons_keyboard(reject_reasons, user_tg_id)

    await callback.message.answer(msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reason")
async def confirm_reject_reason_to_user(callback: CallbackQuery, session: Any, admin: bool) -> None:
    """Подтверждение отправки сообщения об отказе"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    reason_id = int(callback.data.split("|")[1])
    user_tg_id = callback.data.split("|")[2]

    # Получаем причину
    reason: RejectReason = await AsyncOrm.get_reject_reason(reason_id, session)

    # Сообщение админу с подтверждением отмены
    msg = f"<b>\"{reason.reason}\"</b>\n\n{reason.text}"
    keyboard = kb.send_reject_to_user_keyboard(reason, user_tg_id)

    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "send_reason")
async def send_reject_to_user(callback: CallbackQuery, session: Any, bot: Bot, admin: bool) -> None:
    """Отправка сообщения об отказе в верификации"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    reason_id = int(callback.data.split("|")[1])
    user_tg_id = callback.data.split("|")[2]

    # Получаем причину
    reason: RejectReason = await AsyncOrm.get_reject_reason(reason_id, session)

    # Сообщение в группу об отмене верификации
    admin_name = str(callback.from_user.first_name)
    msg = f"\n\n❌ <i>Анкета отклонена администратором \"{admin_name}\"</i>"
    await callback.message.edit_caption(caption=callback.message.caption + msg)

    # Сообщение пользователю об отмене верификации
    user_msg = f"✅ Ваша анкета клиента успешно верифицирована\n\nТеперь вашу анкету будут видеть клиенты/заказчики"

    # Сообщение в группу об отмене верификации

    # Удаление анкеты пользователя

    # Изменение роли пользователя на null
