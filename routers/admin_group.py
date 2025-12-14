import datetime
from typing import Any, List

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile
from database.orm import AsyncOrm
from database.tables import UserRoles
from logger import logger

from middlewares.database import DatabaseMiddleware
from middlewares.admin import AdminMiddleware
from middlewares.private import CheckGroupMessageMiddleware
from routers.keyboards.client_reg import to_main_menu
from routers.messages.executor import executor_card_for_admin_verification, instruction_message
from routers.states.registration import Reject, RejectEdit
from schemas.blocked_users import BlockedUser, BlockedUserAdd
from schemas.executor import RejectReason, Executor
from routers.keyboards import admin as kb
from settings import settings
from utils.datetime_service import convert_date_and_time_to_str

# Роутер для использования в группе
group_router = Router()
# group_router.message.middleware.register(DatabaseMiddleware())
# group_router.callback_query.middleware.register(DatabaseMiddleware())
group_router.message.middleware.register(AdminMiddleware())
group_router.callback_query.middleware.register(AdminMiddleware())
group_router.message.middleware.register(CheckGroupMessageMiddleware())
group_router.callback_query.middleware.register(CheckGroupMessageMiddleware())


# Подтверждение верификации исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_confirm")
async def confirm_executor_registration(callback: CallbackQuery, session: Any, bot: Bot) -> None:
    """Верификация новой анкеты исполнителя в группе"""
    is_admin = await AsyncOrm.check_is_admin(str(callback.from_user.id), session)

    # Проверяем админа
    if not is_admin:
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
    user_msg = f"✅ Поздравляем! Твоя анкета успешно верифицирована\n\n🥳 Теперь анкету будут видеть заказчики"
    await bot.send_message(executor_tg_id, user_msg, message_effect_id="5046509860389126442")

    # Сообщение с инструкцией
    instruction_image = FSInputFile(settings.local_media_path + "instruction2.png")
    caption_msg = instruction_message()
    keyboard = to_main_menu()

    await bot.send_photo(
        executor_tg_id,
        photo=instruction_image,
        caption=caption_msg,
        reply_markup=keyboard.as_markup()
    )


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
    await state.update_data(selected_reasons_periods=[])

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
    period = int(callback.data.split("|")[2])

    # Добавляем или убираем причину из списка
    data = await state.get_data()
    selected_reasons = data["selected_reasons"]
    selected_reasons_periods = data["selected_reasons_periods"]

    # Убираем из списка
    if reason_id in selected_reasons:
        selected_reasons.remove(reason_id)
        selected_reasons_periods.remove(period)
    # Добавляем список
    else:
        selected_reasons.append(reason_id)
        selected_reasons_periods.append(period)

    # Сохраняем обновленный список
    await state.update_data(selected_reasons=selected_reasons)
    await state.update_data(selected_reasons_periods=selected_reasons_periods)

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
    reason_periods = data["selected_reasons_periods"]
    # Берем наибольший период
    period = max(reason_periods)

    # Скидываем стейт
    await state.clear()

    # Получаем причины
    selected_reasons: List[RejectReason] = await AsyncOrm.get_reject_reasons_by_ids(reason_ids, session)

    # Проверяем был ли пользователь уже заблокирован
    blocked_user: BlockedUser = await AsyncOrm.get_blocked_user(user_tg_id, session)

    # Считаем срок блокировки
    expire_date = datetime.datetime.now() + datetime.timedelta(days=period)

    # Если пользователь уже был заблокирован ранее
    if blocked_user:
        # Обновляем ему поле expire_date
        await AsyncOrm.update_blocked_user_expire_date(user_tg_id, expire_date, session)
    # Если его еще не блокировали
    else:
        # Создаем BlockedUser
        user = await AsyncOrm.get_user(user_tg_id, session)
        new_blocked_user = BlockedUserAdd(user_tg_id=user_tg_id, user_id=user.id, expire_date=expire_date)
        await AsyncOrm.create_blocked_user(new_blocked_user, session)

    # Сообщение в группу об отмене верификации
    admin_name = str(callback.from_user.first_name)
    caption_text = data["caption_text"] + f"\n\n❌ <i>Анкета отклонена администратором \"{admin_name}\"\nПричины:\n</i>"
    reasons_text_for_admin = "\n".join([f"\t• {reason.reason}" for reason in selected_reasons])

    await callback.message.edit_caption(caption=caption_text+reasons_text_for_admin)

    # Сообщение пользователю об отмене верификации
    reasons_text_for_user = "\n".join([f"\t• {reason.reason}\n" + f"<i>{reason.text}</i>" for reason in selected_reasons])
    date, time = convert_date_and_time_to_str(expire_date, with_tz=True)
    user_msg = f"😔 К сожалению, твоя анкета не прошла верификацию. " \
               f"Ты можешь повторно заполнить свою анкету и отправить ее на проверку после {date} {time} (МСК).\n\n" \
               f"Причины:\n" \
               f"{reasons_text_for_user}"
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


# Подтверждение изменения анкеты исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_edit_confirm")
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
    executor: Executor = await AsyncOrm.get_executor_by_tg_id(executor_tg_id, session)
    edited_caption = executor_card_for_admin_verification(executor) + f"\n\n<i>Изменения анкеты верифицированы администратором \"{admin_name}\"</i>"
    await callback.message.edit_caption(caption=edited_caption)

    # Оповещаем исполнителя
    user_msg = f"✅ Изменения, внесенные в анкету, верифицированы администратором\n\n"
    keyboard = to_main_menu()
    await bot.send_message(executor_tg_id, user_msg, reply_markup=keyboard.as_markup(), message_effect_id="5046509860389126442")


# Отклонение изменений анкеты исполнителя
@group_router.callback_query(F.data.split("|")[0] == "executor_edit_cancel")
async def cancel_executor_registration(callback: CallbackQuery, session: Any, admin: bool, state: FSMContext) -> None:
    """Отклонение верификации изменений анкеты пользователя"""
    # Убираем клавиатуру сразу после нажатия
    await callback.message.edit_reply_markup(reply_markup=None)

    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Ставим стейт
    await state.set_state(RejectEdit.reason)

    # Сохраняем анкету для дальнейшего использования
    await state.update_data(caption_text=callback.message.caption)

    # Сохраняем tg_id исполнителя
    user_tg_id = callback.data.split("|")[1]
    await state.update_data(user_tg_id=user_tg_id)

    reject_reasons: List[RejectReason] = await AsyncOrm.get_reject_reasons(session)

    # Заготовки для мультиселекта
    await state.update_data(reject_reasons=reject_reasons)
    await state.update_data(selected_reasons=[])
    await state.update_data(selected_reasons_periods=[])

    msg = callback.message.caption + "\n\nВыберите причины отказа изменения анкеты"
    keyboard = kb.select_reasons_keyboard(reject_reasons, [])

    await callback.message.edit_caption(caption=msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reason", RejectEdit.reason)
async def select_reasons(callback: CallbackQuery, state: FSMContext, admin: bool) -> None:
    """Вспомогательный хендлер для мультиселекта"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    reason_id = int(callback.data.split("|")[1])
    period = int(callback.data.split("|")[2])

    # Добавляем или убираем причину из списка
    data = await state.get_data()
    selected_reasons = data["selected_reasons"]
    selected_reasons_periods = data["selected_reasons_periods"]

    # Убираем из списка
    if reason_id in selected_reasons:
        selected_reasons.remove(reason_id)
        selected_reasons_periods.remove(period)
    # Добавляем список
    else:
        selected_reasons.append(reason_id)
        selected_reasons_periods.append(period)

    # Сохраняем обновленный список
    await state.update_data(selected_reasons=selected_reasons)
    await state.update_data(selected_reasons_periods=selected_reasons_periods)

    # Отправляем сообщение
    reject_reasons: List[RejectReason] = data["reject_reasons"]
    caption_text = data["caption_text"]
    msg = caption_text + "\n\nВыберите причины отказа регистрации"
    keyboard = kb.select_reasons_keyboard(reject_reasons, selected_reasons)

    await callback.message.edit_caption(caption=msg, reply_markup=keyboard.as_markup())


@group_router.callback_query(F.data.split("|")[0] == "reject_reasons_done", RejectEdit.reason)
async def send_reject_to_user(callback: CallbackQuery, state: FSMContext, session: Any, bot: Bot, admin: bool) -> None:
    """Отправка сообщения об отказе в верификации изменений"""
    # Проверяем админа
    if not admin:
        await callback.message.answer("⚠️ Функция доступна только администраторам")
        return

    # Получаем данные
    data = await state.get_data()
    reason_ids = data["selected_reasons"]
    reason_periods = data["selected_reasons_periods"]
    # Берем наибольший период
    period = max(reason_periods)
    user_tg_id = data["user_tg_id"]

    # Скидываем стейт
    await state.clear()

    # Получаем причины
    selected_reasons: List[RejectReason] = await AsyncOrm.get_reject_reasons_by_ids(reason_ids, session)

    # Сообщение в группу об отмене верификации
    admin_name = str(callback.from_user.first_name)
    caption_text = data["caption_text"] + f"\n\n❌ <i>Изменения отклонены администратором \"{admin_name}\"\nПричины:\n</i>"
    reasons_text_for_admin = "\n".join([f"\t• {reason.reason}" for reason in selected_reasons])

    await callback.message.edit_caption(caption=caption_text+reasons_text_for_admin)

    # Проверяем был ли пользователь уже заблокирован
    blocked_user: BlockedUser = await AsyncOrm.get_blocked_user(user_tg_id, session)

    # Считаем срок блокировки
    expire_date = datetime.datetime.now() + datetime.timedelta(days=period)

    # Если пользователь уже был заблокирован ранее
    if blocked_user:
        # Обновляем ему поле expire_date
        await AsyncOrm.update_blocked_user_expire_date(user_tg_id, expire_date, session)
    # Если его еще не блокировали
    else:
        # Создаем BlockedUser
        user = await AsyncOrm.get_user(user_tg_id, session)
        new_blocked_user = BlockedUserAdd(user_tg_id=user_tg_id, user_id=user.id, expire_date=expire_date)
        await AsyncOrm.create_blocked_user(new_blocked_user, session)

    # Сообщение пользователю об отмене верификации
    reasons_text_for_user = "\n".join([f"\t• {reason.reason}\n" + f"<i>{reason.text}</i>" for reason in selected_reasons])
    date, time = convert_date_and_time_to_str(expire_date, with_tz=True)
    user_msg = f"😔 К сожалению, твоя анкета не прошла верификацию. " \
               f"Ты можешь повторно заполнить свою анкету и отправить ее на проверку после {date} {time} (МСК).\n\n" \
               f"Причины:\n" \
               f"{reasons_text_for_user}"

    await bot.send_message(user_tg_id, user_msg)

    logger.info(f"Изменение анкеты исполнителя пользователя {user_tg_id} отклонена администратором {admin_name}")