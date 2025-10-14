from typing import Any

from aiogram import Router, types, F, Bot
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm
from database.tables import UserRoles

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckPrivateMessageMiddleware, CheckGroupMessageMiddleware
from schemas.executor import RejectReason
from routers.keyboards import admin as kb
from settings import settings

# Роутер для использования в группе
group_router = Router()
group_router.message.middleware.register(DatabaseMiddleware())
group_router.callback_query.middleware.register(DatabaseMiddleware())
group_router.message.middleware.register(AdminMiddleware())
group_router.callback_query.middleware.register(AdminMiddleware())
group_router.message.middleware.register(CheckGroupMessageMiddleware())
group_router.callback_query.middleware.register(CheckGroupMessageMiddleware())


# Подтверждение верификации исполнителя
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
    edited_caption = callback.message.caption.replace("🚫 Не подтверждена", "✔️ Подтверждена") \
                     + f"\n\n✅ <i>Анкета верифицирована администратором \"{admin_name}\"</i>"
    await callback.message.edit_caption(caption=edited_caption)

    # Оповещаем исполнителя
    user_msg = f"✅ Ваша анкета успешно верифицирована\n\nТеперь вашу анкету будут видеть клиенты/заказчики"
    await bot.send_message(executor_tg_id, user_msg)


# Отказ в верификации исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_cancel")
async def cancel_verification(callback: CallbackQuery, session: Any, admin: bool) -> None:
    """Выбор причины отказа в верификации профиля"""
    # Убираем клавиатуру сразу после нажатия
    await callback.message.edit_reply_markup(reply_markup=None)

    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Получаем tg_id исполнителя
    user_tg_id = callback.data.split("|")[1]

    reject_reasons: list[RejectReason] = await AsyncOrm.get_reject_reasons(session)

    msg = callback.message.caption + "\n\nВыберите причину отказа регистрации"
    keyboard = kb.all_reasons_keyboard(reject_reasons, user_tg_id)

    await callback.message.edit_caption(caption=msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reason")
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
    new_caption_list = callback.message.caption.split("\n\n")
    new_caption_list[1] = f"\n\n❌ <i>Анкета отклонена администратором \"{admin_name}\"</i>" \
                          f"\n<i>Причина: {reason.reason}</i>"
    new_caption = "".join(new_caption_list)
    await callback.message.edit_caption(caption=new_caption)

    # Сообщение пользователю об отмене верификации
    user_msg = f"❌ Верификация вашей анкеты отклонена администратором\n\n" \
               f"<b>Причина: </b>{reason.text}\n\n" \
               f"Для получения получения более подробной информации обратитесь к администратору @{settings.admin_tg_username}"
    await bot.send_message(user_tg_id, user_msg)

    # Изменение роли пользователя на null
    user_role = await AsyncOrm.get_user_role(user_tg_id, session)
    await AsyncOrm.delete_user_role(user_tg_id, session)

    # Удаление анкеты в зависимости от роли
    if user_role == UserRoles.EXECUTOR.value:
        await AsyncOrm.delete_executor(user_tg_id, session)
    elif user_role == UserRoles.CLIENT.value:
        await AsyncOrm.delete_client(user_tg_id, session)
