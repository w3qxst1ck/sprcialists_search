from typing import Any

from aiogram import Router, F, Bot
from aiogram.filters import and_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile

from database.tables import UserRoles
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware
from routers.messages.client import get_client_profile_message
from routers.states.registration import Client
from routers.keyboards.admin import confirm_registration_client_keyboard
from routers.buttons import commands as cmd, buttons as btn
from routers.menu import main_menu

from database.orm import AsyncOrm
from schemas.client import ClientAdd
from settings import settings
from routers.keyboards import client_reg as kb
from utils.download_files import load_photo_from_tg, get_photo_path
from logger import logger
from utils.s3_storage import save_file_to_s3_storage

router = Router()

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())


@router.callback_query(and_f(F.data.split("|")[0] == "choose_role", F.data.split("|")[1] == "client"))
async def start_registration(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Начало регистрации клиента"""
    # Проверка уже выбранной роли у пользователя
    tg_id = str(callback.from_user.id)
    role: str | None = await AsyncOrm.get_user_role(tg_id, session)
    if role:
        role_text = role.capitalize()
        msg = f"У вас уже выбрана роль \"{role_text}\""
        await callback.message.edit_text(msg)
        return

    # Ставим стейт
    await state.set_state(Client.name)

    msg = "Отправьте Имя/ник, который будут видеть другие пользователи"
    keyboard = kb.cancel_keyboard()

    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(Client.name)
async def get_client_name(message: Message, state: FSMContext) -> None:
    """Получаем имя клиента"""
    data = await state.get_data()

    # Меняем предыдущее сообщение
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем имя
    await state.update_data(name=message.text)

    # Меняем стейт
    await state.set_state(Client.client_type)

    # Отправляем сообщение
    msg = "Выберите один из вариантов"

    # Без пропуска описания
    if isinstance(message, Message):
        await message.answer(msg, reply_markup=kb.pick_client_type_keyboard().as_markup())

    # С пропуском описания
    else:
        await message.message.edit_text(msg, reply_markup=kb.pick_client_type_keyboard().as_markup())


@router.callback_query(Client.client_type)
async def get_client_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Получаем тип клиента"""
    client_type = callback.data.split("|")[1]

    # Записываем тип клиента
    await state.update_data(client_type=client_type)

    # Меняем стейт
    await state.set_state(Client.description)

    msg = "Отправьте дополнительную информацию о себе/компании/организации"

    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.message(Client.description)
@router.callback_query(Client.description, F.data == "skip")
async def get_client_description(message: CallbackQuery | Message, state: FSMContext) -> None:
    """Получение описание или пропуск для регитсраиции клиента"""
    data = await state.get_data()

    # Если пользователь отправил описание
    if isinstance(message, Message):
        # Меняем предыдущее сообщение
        try:
            await data["prev_mess"].edit_text(data["prev_mess"].text)
        except Exception:
            pass

        # Если отправлен не текст
        if not message.text:
            prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                             reply_markup=kb.skip_cancel_keyboard().as_markup())
            # Сохраняем предыдущее сообщение
            await state.update_data(prev_mess=prev_mess)
            return

        # Записываем описание клиента
        await state.update_data(description=message.text)

    elif isinstance(message, CallbackQuery):
        # Записываем пустое описание клиента в случае пропуска
        await state.update_data(description=None)

    # Меняем стейт
    await state.set_state(Client.photo)

    # Отправляем сообщение
    msg = "Отправьте фото для вашего профиля"
    keyboard = kb.skip_cancel_keyboard()

    if type(message) == Message:
        prev_mess = await message.answer(msg, reply_markup=keyboard.as_markup())
    else:
        prev_mess = await message.message.edit_text(msg, reply_markup=keyboard.as_markup())

    await state.update_data(prev_mess=prev_mess)


@router.message(Client.photo)
@router.callback_query(F.data == "skip", Client.photo)
async def get_client_photo(message: CallbackQuery | Message, state: FSMContext, bot: Bot) -> None:
    """Получаем фото клиента"""
    data = await state.get_data()

    if isinstance(message, Message):
        # Убираем клавиатуру у предыдущего сообщения
        try:
            await data["prev_mess"].edit_text(data["prev_mess"].text)
        except Exception:
            pass

        # Отправляем сообщение об ожидании
        wait_msg = await message.answer(btn.WAIT_MSG)

        # Проверяем что было отправлено фото
        if not message.photo:
            prev_mess = await wait_msg.edit_text("Неверный формат данных, необходимо отправить фотографию",
                                                 reply_markup=kb.skip_cancel_keyboard().as_markup())
            # Сохраняем предыдущее сообщение
            await state.update_data(prev_mess=prev_mess)
            return

        # Сохраняем фото локально
        await load_photo_from_tg(message, bot, settings.clients_profile_path)

        # Сохраняем информацию фото в стейт
        await state.update_data(photo=True)

    # Если был пропуск выбора фото
    else:
        # Отправляем сообщение об ожидании
        wait_msg = await message.message.edit_text(btn.WAIT_MSG)
        # Сохраняем информацию фото в стейт
        await state.update_data(photo=False)

    # Меняем стейт
    await state.set_state(Client.confirm)

    # Формируем анкету из обязательных полей
    data = await state.get_data()
    client = ClientAdd(
        tg_id=str(message.from_user.id),
        name=data["name"],
        type=data["client_type"],
        description=data["description"],
        photo=data["photo"],
        verified=False,  # без доп верификации
    )
    questionnaire: str = get_client_profile_message(client)

    # Получаем фотографию
    if client.photo:
        filepath = get_photo_path(settings.clients_profile_path, client.tg_id)
    else:
        # Ставим дефолтную если пользователь не загрузил
        filepath = settings.local_media_path + "client.jpg"

    profile_image = FSInputFile(filepath)

    # Сохраняем для дальнейшего использования
    await state.update_data(filepath=filepath)
    await state.update_data(client=client)
    await state.update_data(questionnaire=questionnaire)

    # Отправляем сообщение с фотографией (если она есть)
    msg = f"Ваша анкета готова. Проверьте введенные данные\n\n" \
          f"{questionnaire}\n\n" \
          f"Публикуем? (дополнительную информацию вы можете указать позже в настройках профиля)"

    # Удаляем сообщение об ожидании
    try:
        await wait_msg.delete()
    except Exception:
        pass

    if isinstance(message, Message):
        prev_mess = await message.answer_photo(
            profile_image,
            caption=msg,
            reply_markup=kb.confirm_registration_keyboard().as_markup()
        )
    else:
        prev_mess = await message.message.answer_photo(
            profile_image,
            caption=msg,
            reply_markup=kb.confirm_registration_keyboard().as_markup()
        )

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)

    # Сохраняем фото в s3 хранилище
    if client.photo:
        await save_file_to_s3_storage(filepath, settings.clients_profile_path)


@router.callback_query(Client.confirm, F.data == "confirm_client_registration")
async def confirm_client(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Подтверждение правильности анкеты клиента"""
    # Получаем все данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Предварительная регистрация исполнителя
    client: ClientAdd = data["client"]
    try:
        await AsyncOrm.create_client(client, session)
    except Exception:
        await callback.message.answer(f"Не удалось создать профиль, попробуйте позже или обратитесь к администратору")
        return

    # Убираем клавиатуру у предыдущего сообщения
    try:
        new_caption = get_client_profile_message(client)
        await data["prev_mess"].edit_caption(caption=new_caption)
    except:
        pass

    # Отправка сообщения пользователю
    msg = "✅ Профиль успешно создан\n\nВы можете изменить данные профиля в настройках"
    keyboard = kb.to_main_menu()
    await callback.message.answer(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "cancel_client_registration", StateFilter("*"))
async def cancel_registration(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена регистрации клиента"""
    await state.clear()
    msg = f"Нажмите /{cmd.START[0]}, чтобы начать регистрацию заново"
    await callback.message.edit_text(msg)


@router.callback_query(F.data == "cancel_verification_client", Client.confirm)
async def cancel_verification(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена регистрации клиента на последнем шаге"""
    data = await state.get_data()

    # Удаляем сообщение с анкетой
    try:
        await data["prev_mess"].delete()
    except:
        pass

    # Очищаем стейт
    await state.clear()

    msg = f"Нажмите /{cmd.START[0]}, чтобы начать регистрацию заново"
    await callback.message.answer(msg)


# @router.message(Client.links)
# @router.callback_query(Client.links, F.data == "skip")
# async def get_client_link(message: CallbackQuery | Message, state: FSMContext) -> None:
#     """Получаем отправленную ссылку"""
#     data = await state.get_data()
#
#     # Меняем предыдущее сообщение
#     try:
#         await data["prev_mess"].edit_text(data["prev_mess"].text)
#     except Exception:
#         pass
#
#     # Если ссылка была отправлена
#     if isinstance(message, Message):
#
#         # Если отправлен не текст
#         if not message.text:
#             prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
#                                              reply_markup=kb.skip_cancel_keyboard().as_markup())
#             # Сохраняем предыдущее сообщение
#             await state.update_data(prev_mess=prev_mess)
#             return
#
#         # Если ссылка не валидна
#         if not is_valid_url(message.text):
#             prev_mess = await message.answer(
#                 "Неверный формат ссылки, необходимо отправить текст формата <i>https://www.google.com</i> "
#                 "без дополнительных символов\nОтправьте ссылку заново",
#                 reply_markup=kb.skip_cancel_keyboard().as_markup())
#             # Сохраняем предыдущее сообщение
#             await state.update_data(prev_mess=prev_mess)
#             return
#
#         # Валидную ссылку записываем в память
#         await state.update_data(links=message.text)
#
#     # Сохраняем пустое значение для поля ссылок, если клиент пропустил отправку
#     elif isinstance(message, CallbackQuery):
#         await state.update_data(links=None)
#
#     # Меняем стейт
#     await state.set_state(Client.langs)
#     # Заготовка для мультиселекта
#     await state.update_data(selected_langs=[])
#
#     # Отправляем сообщение
#     msg = "Выберите языки, с которыми вы работаете"
#
#     if isinstance(message, Message):
#         prev_mess = await message.answer(msg, reply_markup=kb.choose_langs_keyboard([]).as_markup())
#
#     else:
#         prev_mess = await message.message.edit_text(msg, reply_markup=kb.choose_langs_keyboard([]).as_markup())
#
#     await state.update_data(prev_mess=prev_mess)
#
#
# @router.callback_query(F.data.split("|")[0] == "choose_langs", Client.langs)
# async def get_langs_multiselect(callback: types.CallbackQuery, state: FSMContext) -> None:
#     """Вспомогательный хэндлер для мультиселекта языков"""
#
#     lang = callback.data.split("|")[1]
#
#     # Получаем дату
#     data = await state.get_data()
#     selected_langs = data["selected_langs"]
#
#     # Добавляем или убираем язык из списка выбранных
#     if lang in selected_langs:
#         # Убираем из выбранных язык
#         selected_langs.remove(lang)
#     else:
#         # Добавляем язык в выбраные
#         selected_langs.append(lang)
#
#     # Сохраняем обновленный список
#     await state.update_data(selected_langs=selected_langs)
#
#     # Отправляем сообщение
#     msg = "Выберите языки, с которыми вы работаете"
#     keyboard = kb.choose_langs_keyboard(selected_langs)
#     prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
#
#     # Сохраняем последнее сообщение
#     await state.update_data(prev_mess=prev_mess)
#
#
# @router.callback_query(F.data == "choose_langs_done", Client.langs)
# async def get_langs(callback: types.CallbackQuery, state: FSMContext) -> None:
#     """Записываем языки, запрашиваем location"""
#     # Сообщение об ожидании
#     wait_msg = await callback.message.edit_text(WAIT_MSG)
#
#     # Меняем стейт
#     await state.set_state(Client.location)
#
#     # Отправляем сообщение
#     msg = "Отправьте ваш город"
#     prev_mess = await wait_msg.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())
#
#     await state.update_data(prev_mess=prev_mess)
#
#
# @router.callback_query(F.data == "skip", Client.location)
# @router.message(Client.location)
# async def get_location(message: CallbackQuery | Message, state: FSMContext) -> None:
#     """Получаем локацию"""
#     data = await state.get_data()
#
#     # Если локация была отправлена
#     if isinstance(message, Message):
#
#         # Если отправлен не текст
#         if not message.text:
#             await data["prev_mess"].edit_text(data["prev_mess"].text)
#             prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
#                                              reply_markup=kb.skip_cancel_keyboard().as_markup())
#             # Сохраняем предыдущее сообщение
#             await state.update_data(prev_mess=prev_mess)
#             return
#
#         await data["prev_mess"].edit_text(data["prev_mess"].text)
#
#         # Валидную ссылку записываем в память
#         await state.update_data(location=message.text)
#
#     # Сохраняем пустое значение для поля ссылок, если клиент пропустил отправку
#     elif isinstance(message, CallbackQuery):
#         await state.update_data(location=None)
#
#     # Меняем стейт
#     await state.set_state(Client.photo)
#
#     # Отправляем сообщение
#     msg = "Отправьте фото профиля"
#     keyboard = kb.skip_cancel_keyboard()
#     if type(message) == Message:
#         prev_mess = await message.answer(msg, reply_markup=keyboard.as_markup())
#     else:
#         prev_mess = await message.message.edit_text(msg, reply_markup=keyboard.as_markup())
#
#     await state.update_data(prev_mess=prev_mess)
