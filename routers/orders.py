import datetime
from typing import Any, List

from aiogram import Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaDocument

from database.orm import AsyncOrm
from middlewares.private import CheckPrivateMessageMiddleware
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.buttons.buttons import WAIT_MSG
from routers.messages.orders import get_order_card_message, get_my_orders_list, order_card_for_edit
from routers.states.orders import CreateOrder
from routers.keyboards import orders as kb
from schemas.client import Client
from schemas.order import OrderAdd, Order, TaskFileAdd
from schemas.profession import Profession, Job
from routers.buttons import buttons as btn
from utils.datetime_service import get_next_and_prev_month_and_year, convert_str_to_datetime, convert_date_time_to_str
from utils.validations import is_valid_price

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


# МЕНЮ МОИ ЗАКАЗЫ
@router.callback_query(F.data.split("|")[1] == "my_orders")
async def my_orders_menu(callback: CallbackQuery, session: Any, state: FSMContext = None) -> None:
    """Меню мои заказы"""
    # Скидываем на всякий случай стейт
    try:
        await state.clear()
    except Exception:
        pass

    # Сообщение об ожидании
    wait_msg = await callback.message.edit_text(btn.WAIT_MSG)

    # Получаем заказы клиента
    tg_id = str(callback.from_user.id)
    orders: List[Order] = await AsyncOrm.get_orders_by_client(tg_id, session)

    # Сообщение
    msg = f"{btn.MY_ORDERS}"
    await callback.answer()
    await wait_msg.edit_text(msg, reply_markup=kb.orders_menu(bool(len(orders))).as_markup())


# РАЗМЕЩЕННЫЕ ЗАКАЗЫ
@router.callback_query(F.data == "my_orders_list")
async def my_orders_list(callback: CallbackQuery, session: Any) -> None:
    """Список размещенных заказов"""
    # Сообщение об ожидании
    wait_msg = await callback.message.edit_text(btn.WAIT_MSG)

    # Получаем заказы клиента
    tg_id = str(callback.from_user.id)
    orders: List[Order] = await AsyncOrm.get_orders_by_client(tg_id, session)

    msg = get_my_orders_list(orders)
    keyboard = kb.my_orders_list_keyboard(orders)
    await callback.answer()
    await wait_msg.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data.split("|")[0] == "my_order")
async def my_order(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Карточка заказа в размещенных заказах"""
    # Скидываем стейт при редакторировании заказа
    try:
        await state.clear()
    except:
        pass

    wait_msg = await callback.message.edit_text(btn.WAIT_MSG)

    # Получаем заказ
    order_id = int(callback.data.split("|")[1])
    order: Order = await AsyncOrm.get_order_by_id(order_id, session)

    # Отправляем сообщение
    msg = order_card_for_edit(order)
    has_files = bool(len(order.files))
    keyboard = kb.my_order_keyboard(order_id, has_files=has_files)
    await callback.answer()
    await wait_msg.edit_text(msg, reply_markup=keyboard.as_markup())


# УДАЛЕНИЕ ЗАКАЗА
@router.callback_query(F.data.split("|")[0] == "delete_order")
async def delete_order(callback: CallbackQuery, session: Any) -> None:
    """Запрос подтверждения удаления заказа"""
    # Получаем заказ
    order_id = int(callback.data.split("|")[1])
    order: Order = await AsyncOrm.get_order_by_id(order_id, session)

    # Отправляем сообщение
    msg = f"Удалить заказ <b>\"{order.title}\"</b>?"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.delete_order_confirm_keyboard(order_id).as_markup())


@router.callback_query(F.data.split("|")[0] == "delete_order_confirmed")
async def delete_order_confirmed(callback: CallbackQuery, session: Any) -> None:
    """Удаление заказа"""
    # Получаем order_id
    order_id = int(callback.data.split("|")[1])

    # Удаляем заказ
    await AsyncOrm.delete_order(order_id, session)

    # Отправляем сообщение
    msg = f"✅ Заказ удален"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.confirmed_create_order_keyboard().as_markup())


# СКАЧИВАНИЕ ФАЙЛОВ ЗАКАЗА
@router.callback_query(F.data.split("|")[0] == "download_files")
async def download_files(callback: CallbackQuery, session: Any) -> None:
    """Отправка пользователю файлов заказа"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Получаем заказ
    order_id = int(callback.data.split("|")[1])
    order: Order = await AsyncOrm.get_order_by_id(order_id, session)

    # Отправляем файлы
    files = [InputMediaDocument(media=file.file_id) for file in order.files]
    try:
        await callback.message.answer_media_group(media=files)
    except Exception:
        await callback.message.answer(f"{btn.INFO} Ошибка при отправке файлов. Повтори запрос позже")
    finally:
        # Отправляем сообщение карточки заказа
        msg = get_order_card_message(order)
        has_files = bool(len(order.files))
        keyboard = kb.my_order_keyboard(order_id, has_files=has_files)
        await callback.message.answer(msg, reply_markup=keyboard.as_markup())


# СОЗДАНИЕ ЗАКАЗА
@router.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Начало создания заказа"""
    # Устанавливаем стейт
    await state.set_state(CreateOrder.profession)

    # Получаем все профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выбери направление для создания заказа"
    keyboard = kb.profession_keyboard(professions)
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", CreateOrder.profession)
async def get_profession(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получение профессии, запрос jobs"""
    # Записываем профессию
    profession_id = int(callback.data.split("|")[1])
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(CreateOrder.jobs)

    # Получаем все jobs по профессии
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Вспомогательные данные для мультиселекта
    await state.update_data(selected_jobs=[])
    await state.update_data(all_jobs=jobs)

    # Запрашиваем jobs
    msg = "Выбери категории (до 3 штук)"
    keyboard = kb.select_jobs_keyboard(jobs, [])
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "select_jobs", CreateOrder.jobs)
async def get_jobs_multiselect(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
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
    msg = callback.message.text
    keyboard = kb.select_jobs_keyboard(all_jobs, selected_jobs)
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "select_jobs_done", CreateOrder.jobs)
async def get_jobs(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение jobs, запрос названия"""
    # Меняем стейт
    await state.set_state(CreateOrder.title)

    # Запрашиваем название
    msg = "Отправь название (заголовок) заказа"
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(CreateOrder.title)
async def get_title(message: Message, state: FSMContext) -> None:
    """Получаем название, запрашиваем ТЗ"""
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

    # Записываем название
    await state.update_data(title=message.text)

    # Меняем стейт
    await state.set_state(CreateOrder.task)

    # Отправляем сообщение
    msg = "Отправь краткое ТЗ"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(CreateOrder.task)
async def get_task(message: Message, state: FSMContext) -> None:
    """Получаем ТЗ, запрашиваем цену"""
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

    # Если текст длиннее 1000 символов
    if len(message.text) > 1000:
        prev_mess = await message.answer(f"Текст должен быть не более 1000 символов, вы отправили {len(message.text)}",
                                         reply_markup=kb.cancel_keyboard().as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Записываем ТЗ
    await state.update_data(task=message.text)

    # Заготовка на пропуск цены
    await state.update_data(price=None)

    # Меняем стейт
    await state.set_state(CreateOrder.price)

    # Отправляем сообщение
    msg = "Отправь цену заказа в рублях (например: 2000) или нажмите \"Пропустить\""
    prev_mess = await message.answer(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(CreateOrder.price)
@router.callback_query(F.data == "skip", CreateOrder.price)
async def get_price(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Получаем цену, запрашиваем дедлайн"""
    # Если ввели цену
    if type(message) == Message:
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

        # Если ввели не корректное число
        if not is_valid_price(message.text):
            prev_mess = await message.answer("Неверный формат данных, необходимо отправить только число без других символов",
                                             reply_markup=kb.skip_cancel_keyboard().as_markup())
            # Сохраняем предыдущее сообщение
            await state.update_data(prev_mess=prev_mess)
            return

        # Записываем цену
        await state.update_data(price=message.text)

    # Меняем стейт
    await state.set_state(CreateOrder.deadline)

    # Готовим клавиатуру-календарь
    now_year = datetime.datetime.now().year
    now_month = datetime.datetime.now().month
    dates_data = get_next_and_prev_month_and_year(now_month, now_year)
    calendar = kb.calendar_keyboard(now_year, now_month, dates_data, need_prev_month=False)

    # Отправляем сообщение
    msg = "Укажи срок выполнения заказа с помощью клавиатуры ниже"

    # Без пропуска цены
    if type(message) == Message:
        prev_mess = await message.answer(msg, reply_markup=calendar.as_markup())
    # С пропуском цены
    else:
        await message.answer()
        prev_mess = await message.message.edit_text(msg, reply_markup=calendar.as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "action", CreateOrder.deadline)
async def action_calendar(callback: CallbackQuery, state: FSMContext) -> None:
    """Вспомогательный хендлер для перелистывания календаря"""
    # Получаем текущий месяц
    now_month = datetime.datetime.now().month

    # Получаем месяц и год для отрисовки календаря
    month = int(callback.data.split("|")[1])
    year = int(callback.data.split("|")[2])

    # Данные для отрисовки календаря
    dates_data = get_next_and_prev_month_and_year(month, year)

    # Нужен ли предыдущий месяц
    need_prev_month = month > now_month

    # Меняем клавиатуру
    text = callback.message.text
    calendar = kb.calendar_keyboard(year, month, dates_data, need_prev_month=need_prev_month)
    await callback.answer()
    prev_mess = await callback.message.edit_text(text, reply_markup=calendar.as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "select_deadline", CreateOrder.deadline)
async def get_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    """Запись дедлайна, запрос требований"""
    # Получаем дату и переводим в формат datetime
    deadline_str = callback.data.split("|")[1]
    deadline = convert_str_to_datetime(deadline_str)

    # Проверяем чтобы дата была не раньше сегодня
    if deadline.date() <= datetime.datetime.now().date():
        # Удаляем сообщение
        data = await state.get_data()
        try:
            await data["prev_mess"].delete()
        except Exception:
            pass

        # Готовим клавиатуру
        now_year = datetime.datetime.now().year
        now_month = datetime.datetime.now().month
        dates_data = get_next_and_prev_month_and_year(now_month, now_year)
        calendar = kb.calendar_keyboard(now_year, now_month, dates_data, need_prev_month=False)

        date = convert_date_time_to_str(datetime.datetime.now())
        msg = f"❗ Выбрана неверная дата, необходимо выбрать дату не ранее чем {date}"
        prev_mess = await callback.message.answer(msg, reply_markup=calendar.as_markup())

        # Сохраняем сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем дату
    await state.update_data(deadline=deadline)

    # Меняем стейт
    await state.set_state(CreateOrder.files)

    # Заготовка для файлов
    await state.update_data(file_ids=[])
    await state.update_data(filenames=[])

    # Отправляем сообщение
    msg = "При необходимости отправь <b>отдельными сообщениями</b> файлы (например с более подробным описанием ТЗ к задаче) или нажмите \"Пропустить\""
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(CreateOrder.files)
async def get_file(message: Message, state: FSMContext) -> None:
    """Вспомогательный хендлер для получения файлов"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].html_text)
    except Exception:
        pass

    # Если отправлен не файл
    if not message.document:
        # Проверяем может ли пользователь продолжить (если есть хотя бы один файл)
        if len(data["file_ids"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_keyboard()

        prev_mess = await message.answer("Неверный формат данных. Необходимо отправить файл расширения "
                                         ".pdf, .docx, .xlsx, .txt, либо jpeg/jpg/png (отправленные файлом)",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если фал больше 10МБ
    if message.document.file_size > 100_000_000:
        # Проверяем может ли пользователь продолжить (если есть хотя бы один файл)
        if len(data["file_ids"]) != 0:
            keyboard = kb.continue_cancel_keyboard()
        else:
            keyboard = kb.cancel_keyboard()

        prev_mess = await message.answer("Размер файла не должен быть более 100МБ. Отправьте файл или нажмите \"Продолжить\"",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем если уже есть три файла
    if len(data["file_ids"]) == 3:
        prev_mess = await message.answer(
            "Уже отправлено 3 файла, нажмите \"Продолжить\"",
            reply_markup=kb.continue_cancel_keyboard().as_markup()
        )
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Сохраняем ids файл в стейт
    file_ids = data["file_ids"]
    file_ids.append(message.document.file_id)
    await state.update_data(file_ids=file_ids)

    # Сохраняем names файл в стейт
    filenames = data["filenames"]
    filenames.append(message.document.file_name)
    await state.update_data(filenames=filenames)
    filenames_text = ", ".join(filenames)

    # Отправляем сообщение
    msg = f"Отправь следующий файл или нажми кнопку \"Продолжить\"\n\n" \
          f"Отправлено файлов {len(file_ids)}/3:\n{filenames_text}"
    prev_mess = await message.answer(msg, reply_markup=kb.continue_cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(or_f(F.data == "continue", F.data == "skip"), CreateOrder.files)
async def get_files(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос требований"""
    # Меняем стейт
    await state.set_state(CreateOrder.requirements)

    # Заготовка под пропуск требований
    await state.update_data(requirements=None)

    # Отправляем сообщение
    msg = "Отправь сообщением особые требования к задаче или нажмите \"Пропустить\""
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=kb.skip_cancel_keyboard().as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "skip", CreateOrder.requirements)
@router.message(CreateOrder.requirements)
async def get_requirements(message: Message | CallbackQuery, state: FSMContext, session: Any) -> None:
    """Получение требований, предпросмотр"""
    # Если ввели требования
    if type(message) == Message:
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

        # Записываем требования
        await state.update_data(requirements=message.text)

    # Меняем стейт
    await state.set_state(CreateOrder.confirmation)

    # Сообщение об ожидании
    if type(message) == Message:
        wait_msg = await message.answer(WAIT_MSG)
    else:
        await message.answer()
        wait_msg = await message.message.edit_text(WAIT_MSG)

    # Получаем дату
    data = await state.get_data()

    # Формируем заказ для предпросмотра
    profession: Profession = await AsyncOrm.get_profession(data["profession_id"], session)
    jobs: List[Job] = await AsyncOrm.get_jobs_by_ids(data["selected_jobs"], session)
    tg_id = str(message.from_user.id)
    client: Client = await AsyncOrm.get_client(tg_id, session)

    # Создаем схемы файлов
    files: List[TaskFileAdd] = []
    for idx in range(len(data["filenames"])):
        file = TaskFileAdd(
            file_id=data["file_ids"][idx],
            filename=data["filenames"][idx]
        )
        files.append(file)

    # вычисляем дедлайн (берем только даты без времени)
    period = (data["deadline"].date() - datetime.datetime.now().date()).days

    order = OrderAdd(
        client_id=client.id,
        tg_id=tg_id,
        profession=profession,
        jobs=jobs,
        title=data["title"],
        task=data["task"],
        price=data["price"],
        period=period,
        requirements=data["requirements"],
        created_at=datetime.datetime.now(),
        is_active=True,
        files=files,
    )

    # Сохраняем заказ в стейте
    await state.update_data(order=order)

    # Отправляем сообщение
    order_card = get_order_card_message(order)
    msg = f"Проверь введенные данные\n\n" \
          f"{order_card}\n\n" \
          f"Публикуем?"
    keyboard = kb.confirm_create_order_keyboard()
    await wait_msg.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "confirm_create_order")
async def confirm_create_order(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Создание заказа"""
    # Получаем данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохраняем заказ в БД
    try:
        await AsyncOrm.create_order(data["order"], session)
    except Exception:
        msg = f"{btn.INFO} Ошибка при размещении заказа. Повтори попытку позже"
        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=kb.confirmed_create_order_keyboard().as_markup())
        return

    # Отправляем сообщение пользователю
    msg = "✅ Твой заказ успешно размещен. Теперь его будут видеть исполнители"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.confirmed_create_order_keyboard().as_markup())


