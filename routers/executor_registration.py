import datetime
from typing import Any, List

from aiogram import Router, types, F, Bot
from aiogram.filters import and_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from database.tables import Availability
from middlewares.database import DatabaseMiddleware
from middlewares.private import CheckPrivateMessageMiddleware
from routers.messages.executor import executor_card_for_admin_verification
from routers.states.registration import Executor

from routers.buttons import commands as cmd
from routers.buttons.buttons import WAIT_MSG, INFO
from routers.keyboards.admin import confirm_registration_executor_keyboard

from database.orm import AsyncOrm
from schemas.blocked_users import BlockedUser
from schemas.executor import ExecutorAdd
from schemas.profession import Job, Profession
from schemas.user import User
from utils.datetime_service import convert_date_and_time_to_str
from utils.download_files import load_photo_from_tg, get_photo_path
from settings import settings
from routers.keyboards import executor_registration as kb
from utils.validations import is_valid_age, is_valid_url

router = Router()
router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())
# router.message.middleware.register(DatabaseMiddleware())
# router.callback_query.middleware.register(DatabaseMiddleware())


@router.callback_query(and_f(F.data.split("|")[0] == "choose_role", F.data.split("|")[1] == "executor"))
async def start_registration(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Начало регистрации исполнителя"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Проверка уже выбранной роли у пользователя
    tg_id = str(callback.from_user.id)
    role: str | None = await AsyncOrm.get_user_role(tg_id, session)
    if role:
        role_text = settings.roles[role]
        msg = f"У тебя уже выбрана роль {role_text}"
        await callback.answer()
        await callback.message.answer(msg)
        return

    # Проверка заблокирован ли пользователь
    blocked_user: BlockedUser = await AsyncOrm.get_blocked_user(tg_id, session)

    if blocked_user:
        # Проверяем срок блокировки
        # Если срок еще не вышел
        if blocked_user.expire_date > datetime.datetime.now():
            date, time = convert_date_and_time_to_str(blocked_user.expire_date, with_tz=True)
            msg = f"Повторная регистрация будет доступна после {date} {time} (МСК)"
            await callback.answer()
            await callback.message.answer(msg)
            return

    # Записываем роль
    await state.update_data(role="исполнитель")

    # Ставим стейт
    await state.set_state(Executor.name)

    # Отправляем сообщение
    msg = "Давай оформим твой профиль\n\nНапиши свое имя"
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.name)
async def get_name(message: types.Message, state: FSMContext) -> None:
    """Запись имени, запрос возраста"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
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
    await state.set_state(Executor.photo)

    # Отправляем сообщение с запросом аватара
    msg = "Отправь фото профиля"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.photo)
async def get_photo(message: types.Message, bot: Bot, state: FSMContext) -> None:
    """Получение фото, запрос возраста"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Проверяем что отправлено фото
    if not message.photo:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить фотографию",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем фото локально
    await load_photo_from_tg(message, bot, settings.executors_profile_path)

    # Сохраняем фото в стейт
    await state.update_data(photo=True)

    # Меняем стейт
    await state.set_state(Executor.age)

    # Отправляем сообщение
    msg = "Напиши свой возраст"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.age)
async def get_age(message: types.Message, session: Any, state: FSMContext) -> None:
    """Получение возраста, запрос профессии"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если возраст введен некорректный
    if not is_valid_age(message.text):
        prev_mess = await message.answer("Необходимо отправить возраст одним числом от 18 до 100",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем возраст
    await state.update_data(age=int(message.text))

    # Меняем стейт
    await state.set_state(Executor.profession)

    # Получаем доступные профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выбери направление"
    prev_mess = await message.answer(msg, reply_markup=kb.profession_keyboard(professions).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", Executor.profession)
async def get_profession(callback: types.CallbackQuery, session: Any, state: FSMContext) -> None:
    """Получение профессии, запрос Job"""
    profession_id = int(callback.data.split("|")[1])

    # Записываем профессию
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(Executor.jobs)

    # Получаем Jobs для профессии
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Заготовка для мультиселекта
    selected_jobs = []

    # Записываем все Jobs и заготовку выбранных Jobs в стейт, чтобы каждый раз не получать заново
    await state.update_data(all_jobs=jobs)
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выбери категории (до 3 вариантов)"
    keyboard = kb.jobs_keyboard(jobs, selected_jobs)
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "choose_jobs", Executor.jobs)
async def get_jobs_multiselect(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Вспомогательный хендлер для мультиселекта"""
    job_id = int(callback.data.split("|")[1])

    # Получаем данные из стейта
    data = await state.get_data()
    selected_jobs = data["selected_jobs"]
    all_jobs = data["all_jobs"]

    # Добавляем или удаляем Job из списка выбранных
    if job_id in selected_jobs:
        selected_jobs.remove(job_id)
    else:
        # Убираем одну если больше 3
        if len(selected_jobs) == 3:
            selected_jobs[0] = job_id
        else:
            selected_jobs.append(job_id)

    # Обновляем выбранные работы в стейте
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выбери категории (до 3 вариантов)"
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs)
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "choose_jobs_done", Executor.jobs)
async def get_jobs(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Запись Jobs после мультиселекта, запрос описания"""
    # Меняем стейт
    await state.set_state(Executor.description)

    # Отправляем сообщение
    msg = "Отправь информацию о себе (не более 500 символов)"
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.description)
async def get_description(message: types.Message, state: FSMContext) -> None:
    """Получение описания, запрос ставки"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если текст длиннее 500 символов
    if len(message.text) > 500:
        prev_mess = await message.answer(f"Текст должен быть не более 500 символов, вы отправили {len(message.text)}",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем текст
    await state.update_data(description=message.text)

    # Меняем стейт
    await state.set_state(Executor.rate)

    # Отправляем сообщение
    msg = "Напиши свой прайс (например: 2 000 ₽/час или 30 000 ₽/месяц)"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.rate)
async def get_rate(message: types.Message, state: FSMContext) -> None:
    """Получаем ставку, запрашиваем опыт"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Записываем ставку
    await state.update_data(rate=message.text)

    # Меняем стейт
    await state.set_state(Executor.experience)

    # Отправляем сообщение
    msg = "Укажи опыт по выбранному направлению (например: 5 лет)"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.experience)
async def get_experience(message: types.Message, state: FSMContext) -> None:
    """Получаем опыт, запрашиваем ссылки на портфолио"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Записываем опыт
    await state.update_data(experience=message.text)

    # Делаем заготовку под ссылки
    await state.update_data(links=[])

    # Меняем стейт
    await state.set_state(Executor.links)

    # Отправляем сообщение
    msg = "Отдельными сообщениями отправь ссылки на портфолио"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.links)
async def get_link(message: types.Message, state: FSMContext) -> None:
    """Вспомогательный хэндлер для получения ссылок на портфолио"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text, disable_web_page_preview=True)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        # Проверяем может ли пользователь продолжить (если есть хотя бы одна валидная ссылка)
        if len(data["links"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_keyboard()

        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если ссылка не валидна
    if not is_valid_url(message.text):
        # Проверяем может ли пользователь продолжить (если есть хотя бы одна валидная ссылка)
        if len(data["links"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_keyboard()

        prev_mess = await message.answer("Неверный формат ссылки! Необходимо отправить текст формата https://www.google.com без дополнительных символов.\n"
                                         "Отправь ссылку заново",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Записываем ссылку
    links = data["links"]
    links.append(message.text)
    links_text = "\n".join([f"{link}" for link in links])
    links_count = len(links)
    await state.update_data(links=links)

    # Отправляем сообщение
    msg = f"Отправь следующую ссылку или нажми кнопку \"Продолжить\"\n\n" \
          f"Отправлено ссылок {links_count} шт.:\n{links_text}"
    prev_mess = await message.answer(msg, reply_markup=kb.continue_cancel_keyboard().as_markup(), disable_web_page_preview=True)

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "continue", Executor.links)
async def get_links(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Получаем список ссылок на портфолио, запрашиваем контакты"""
    # Меняем стейт
    await state.set_state(Executor.contacts)

    # Заготовка на случай пропуска контактов
    await state.update_data(contacts=None)

    # Отправляем сообщение
    msg = "Отправь контакт для связи (например телефон: 8-999-888-77-66)\n\n" \
          "❗<b>Важно</b>: указанные контакты будут видны другим пользователям сервиса"
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем последнее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.contacts)
# Если пропускают контакты
@router.callback_query(F.data == "skip", Executor.contacts)
async def get_contacts(message: types.Message | types.CallbackQuery, state: FSMContext) -> None:
    """Получаем контакты, запрашиваем город"""
    # Если ввели контакты
    if type(message) == types.Message:
        # Меняем предыдущее сообщение
        data = await state.get_data()
        try:
            await data["prev_mess"].edit_text(data["prev_mess"].text, disable_web_page_preview=True)
        except Exception:
            pass

        # Если отправлен не текст
        if not message.text:
            prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                             reply_markup=kb.skip_cancel_keyboard().as_markup())
            # Сохраняем предыдущее сообщение
            await state.update_data(prev_mess=prev_mess)
            return

        # Записываем контакты
        await state.update_data(contacts=message.text)

    # Меняем стейт
    await state.set_state(Executor.location)

    # Заготовка на случай пропуска города
    await state.update_data(location=None)

    # Отправляем сообщение
    msg = "Напиши свой город"

    # Без пропуска контактов
    if type(message) == types.Message:
        prev_mess = await message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # С пропуском контактов
    else:
        await message.answer()
        prev_mess = await message.message.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(Executor.location)
# Если пропускают город
@router.callback_query(F.data == "skip", Executor.location)
async def get_location(message: types.Message | types.CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получаем город, предпросмотр"""
    # Если город был отправлен
    if type(message) == types.Message:
        # Меняем предыдущее сообщение
        data = await state.get_data()
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

        # Записываем город
        await state.update_data(location=message.text)

        # Wait message
        wait_msg = await message.answer(WAIT_MSG)

    # Если город пропущен
    else:
        await message.answer()
        wait_msg = await message.message.edit_text(WAIT_MSG)

    # Меняем стейт
    await state.set_state(Executor.verification)

    # Получаем все введенные данные
    data = await state.get_data()

    # Формируем анкету
    profession: Profession = await AsyncOrm.get_profession(data["profession_id"], session)
    jobs: List[Job] = await AsyncOrm.get_jobs_by_ids(data["selected_jobs"], session)
    executor = ExecutorAdd(
        tg_id=str(message.from_user.id),
        name=data["name"],
        age=data["age"],
        description=data["description"],
        rate=data["rate"],
        experience=data["experience"],
        links=data["links"],
        availability=Availability.FREE,
        contacts=data["contacts"],
        location=data["location"],
        photo=data["photo"],
        profession=profession,
        jobs=jobs,
        verified=False
    )
    questionnaire = executor_card_for_admin_verification(executor)

    # Сохраняем для дальнейшего использования
    await state.update_data(executor=executor)
    await state.update_data(questionnaire=questionnaire)

    # Получаем фотографию
    filepath = get_photo_path(settings.executors_profile_path, executor.tg_id)
    profile_image = FSInputFile(filepath)
    await state.update_data(filepath=filepath)

    # Удаляем сообщение об ожидании
    try:
        await wait_msg.delete()
    except Exception:
        pass

    # Отправляем сообщение с фотографией
    msg = f"Твоя анкета готова. Проверь введенные данные\n\n" \
          f"{questionnaire}\n\n" \
          f"Публикуем?"

    # Если был отправлен город
    if isinstance(message, types.Message):
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


@router.callback_query(F.data == "confirm_registration", Executor.verification)
async def registration_confirmation(callback: types.CallbackQuery, state: FSMContext, session: Any, bot: Bot) -> None:
    """Подтверждение регистрации"""
    # Убираем клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Получаем все данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Предварительная регистрация исполнителя и изменение роли пользователя на исполнителя
    executor: ExecutorAdd = data["executor"]
    try:
        await AsyncOrm.create_executor(executor, session)
        # Отправка сообщения пользователю
        user_msg = f"{INFO} Анкета на проверке. Мы напишем сразу после верификации, обычно это занимает до 24 часов"
        await callback.message.answer(user_msg)
    except:
        await callback.message.answer(f"{INFO} Ошибка при регистрации, попробуй позже")
        return

    # Отправляем в группу анкету на согласование
    admin_group_id = settings.admin_group_id
    profile_image = FSInputFile(data["filepath"])
    admin_msg = data["questionnaire"]
    await bot.send_photo(
        admin_group_id,
        photo=profile_image,
        caption=admin_msg,
        reply_markup=confirm_registration_executor_keyboard(executor.tg_id).as_markup(),
    )


@router.callback_query(F.data == "cancel_executor_registration", StateFilter("*"))
async def cancel_registration(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Отмена регистрации"""
    await state.clear()
    msg = f"Нажми /{cmd.START[0]}, чтобы начать регистрацию заново"

    try:
        await callback.answer()
        await callback.message.edit_text(msg)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(msg)

