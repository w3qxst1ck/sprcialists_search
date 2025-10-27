from typing import Any, List

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from database.orm import AsyncOrm
from database.tables import UserRoles
from logger import logger

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckGroupMessageMiddleware
from routers.keyboards.client_reg import to_main_menu
from routers.states.registration import Reject
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
    keyboard = to_main_menu()
    await bot.send_message(executor_tg_id, user_msg, reply_markup=keyboard.as_markup(), message_effect_id="5046509860389126442")


# Отказ в верификации исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_cancel")
async def cancel_verification(callback: CallbackQuery, session: Any, admin: bool, state: FSMContext) -> None:
    """Выбор причины отказа в верификации профиля"""
    # Убираем клавиатуру сразу после нажатия
    await callback.message.edit_reply_markup(reply_markup=None)

    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Ставим стейт
    await state.set_state(Reject.reason)

    # Сохраняем анкету для дальнейшего использования
    await state.update_data(caption_text=callback.message.caption)

    # Сохраняем tg_id исполнителя
    user_tg_id = callback.data.split("|")[1]
    await state.update_data(user_tg_id=user_tg_id)

    reject_reasons: List[RejectReason] = await AsyncOrm.get_reject_reasons(session)

    # Заготовки для мультиселекта
    await state.update_data(reject_reasons=reject_reasons)
    await state.update_data(selected_reasons=[])

    msg = callback.message.caption + "\n\nВыберите причины отказа регистрации"
    keyboard = kb.select_reasons_keyboard(reject_reasons, [])

    await callback.message.edit_caption(caption=msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reason", Reject.reason)
async def select_reasons(callback: CallbackQuery, state: FSMContext, admin: bool) -> None:
    """Вспомогательный хендлер для мультиселекта"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    reason_id = int(callback.data.split("|")[1])

    # Добавляем или убираем причину из списка
    data = await state.get_data()
    selected_reasons = data["selected_reasons"]

    # Убираем из списка
    if reason_id in selected_reasons:
        selected_reasons.remove(reason_id)
    # Добавляем список
    else:
        selected_reasons.append(reason_id)

    # Сохраняем обновленный список
    await state.update_data(selected_reasons=selected_reasons)

    # Отправляем сообщение
    reject_reasons: List[RejectReason] = data["reject_reasons"]
    caption_text = data["caption_text"]
    msg = caption_text + "\n\nВыберите причины отказа регистрации"
    keyboard = kb.select_reasons_keyboard(reject_reasons, selected_reasons)

    await callback.message.edit_caption(caption=msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reasons_done", Reject.reason)
async def send_reject_to_user(callback: CallbackQuery, state: FSMContext, session: Any, bot: Bot, admin: bool) -> None:
    """Отправка сообщения об отказе в верификации"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Получаем данные
    data = await state.get_data()
    reason_ids = data["selected_reasons"]
    user_tg_id = data["user_tg_id"]

    # Скидываем стейт
    await state.clear()

    # Получаем причины
    selected_reasons: List[RejectReason] = await AsyncOrm.get_reject_reasons_by_ids(reason_ids, session)

    # Сообщение в группу об отмене верификации
    admin_name = str(callback.from_user.first_name)
    caption_text = data["caption_text"] + f"\n\n❌ <i>Анкета отклонена администратором \"{admin_name}\"\nПричины:\n</i>"
    reasons_text_for_admin = "\n".join([f"\t• {reason.reason}" for reason in selected_reasons])

    await callback.message.edit_caption(caption=caption_text+reasons_text_for_admin)

    # Сообщение пользователю об отмене верификации
    reasons_text_for_user = "\n".join([f"\t• {reason.reason}\n" + f"<i>{reason.text}</i>" for reason in selected_reasons])
    user_msg = f"❌ Верификация вашей анкеты отклонена администратором\n\n" \
               f"<b>Причины:\n</b>{reasons_text_for_user}\n\n" \
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

    logger.info(f"Анкета исполнителя пользователя {user_tg_id} отклонена администратором {admin_name}")
