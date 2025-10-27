from typing import Any, List

from aiogram import Router, F
from aiogram.filters import or_f, and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from middlewares.private import CheckPrivateMessageMiddleware
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.states.orders import EditOrderProfession, EditOrderTitle, EditOrderTask, EditOrderPrice, EditOrderDeadline, \
    EditOrderRequirements, EditOrderFiles
from routers.keyboards import edit_order as kb
from schemas.order import TaskFileAdd
from schemas.profession import Profession, Job
from routers.buttons import buttons as btn
from utils.validations import is_valid_price, is_valid_deadline

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


# ИЗМЕНЕНИЕ ПРОФЕССИИ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "profession"))
async def edit_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Изменение profession"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderProfession.profession)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Получаем доступные профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выберите раздел для заказа"
    prev_mess = await callback.message.answer(msg, reply_markup=kb.profession_keyboard(professions, order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", EditOrderProfession.profession)
async def get_profession(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Получение профессии, запрос Job"""
    profession_id = int(callback.data.split("|")[1])

    # Получаем дату
    data = await state.get_data()

    # Записываем профессию
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(EditOrderProfession.jobs)

    # Получаем Jobs для профессии
    jobs: List[Job] = await AsyncOrm.get_jobs_by_profession(profession_id, session)

    # Заготовка для мультиселекта
    selected_jobs = []

    # Записываем все Jobs и заготовку выбранных Jobs в стейт, чтобы каждый раз не получать заново
    await state.update_data(all_jobs=jobs)
    await state.update_data(selected_jobs=selected_jobs)

    # Отправляем сообщение
    msg = "Выберите подкатегории для создания заказа (до 3 штук)"
    keyboard = kb.jobs_keyboard(jobs, selected_jobs, order_id=data["order_id"])
    await callback.answer()
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_jobs", EditOrderProfession.jobs)
async def get_jobs_multiselect(callback: CallbackQuery, state: FSMContext) -> None:
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
    keyboard = kb.jobs_keyboard(all_jobs, selected_jobs, data["order_id"])
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "choose_jobs_done", EditOrderProfession.jobs)
async def get_jobs(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Запись Jobs после мультиселекта"""
    # Получаем дату
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Меняем профессии и jobs в БД
    jobs_ids = data["selected_jobs"]
    try:
        await AsyncOrm.update_order_profession(data["order_id"], jobs_ids, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении профессий. Повторите запрос позже"
        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = f"✅ Разделы профессий в заказе успешно изменены"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ НАЗВАНИЯ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "title"))
async def edit_title(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение названия"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderTitle.title)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте название (заголовок) заказа"
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderTitle.title)
async def get_title(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем название"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_title(data["order_id"], message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении названия заказа. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Название заказа успешно изменено"
    await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ ТЗ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "task"))
async def edit_task(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение ТЗ"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderTask.task)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте краткое ТЗ"
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderTask.task)
async def get_task(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем ТЗ"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если текст длиннее 1000 символов
    if len(message.text) > 1000:
        prev_mess = await message.answer(f"Текст должен быть не более 1000 символов, вы отправили {len(message.text)}",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_task(data["order_id"], message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении ТЗ заказа. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Краткое ТЗ заказа успешно изменено"
    await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ ЦЕНЫ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "price"))
async def edit_price(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение цены"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderPrice.price)

    # Заготовка на пропуск цены
    await state.update_data(price=None)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте цену заказа в рублях (например: 2000) или нажмите \"Оставить пустым\""
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_skip_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderPrice.price)
async def get_price(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем цену"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если ввели не корректное число
    if not is_valid_price(message.text):
        prev_mess = await message.answer(
            "Неверный формат данных, необходимо отправить только число без других символов",
            reply_markup=kb.cancel_skip_edit_order_keyboard(data["order_id"]).as_markup()
        )
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_price(data["order_id"], message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении цены заказа. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Цена заказа успешно изменена"
    await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


@router.callback_query(F.data == "skip", EditOrderPrice.price)
async def skip_price(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись цены пустой"""
    # Получаем данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_price(data["order_id"], None, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении цены заказа. Повторите запрос позже"
        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Цена заказа успешно изменена"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ СРОКА
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "deadline"))
async def edit_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение срока заказа"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderDeadline.deadline)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте <b>цифрой</b> количество дней на выполнение заказа"
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderDeadline.deadline)
async def get_deadline(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем ТЗ"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Если невалидный срок
    if not is_valid_deadline(message.text):
        prev_mess = await message.answer(f"Необходимо отправить количество дней цифрой без других символов. Срок не может быть меньше 1 дня.",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_period(data["order_id"], int(message.text), session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении срока заказа. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Срок заказа успешно изменено"
    await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ ТРЕБОВАНИЙ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "requirements"))
async def edit_requirements(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение требований"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderRequirements.requirements)

    # Заготовка на пропуск требований
    await state.update_data(requirements=None)

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте сообщение особые требования к задаче или нажмите \"Оставить пустым\""
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_skip_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderRequirements.requirements)
async def get_requirements(message: Message, state: FSMContext, session: Any) -> None:
    """Получаем требования"""
    # Меняем предыдущее сообщение
    data = await state.get_data()
    try:
        await data["prev_mess"].edit_text(data["prev_mess"].text)
    except Exception:
        pass

    # Если отправлен не текст
    if not message.text:
        prev_mess = await message.answer("Неверный формат данных, необходимо отправить текст",
                                         reply_markup=kb.cancel_edit_order_keyboard(data["order_id"]).as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_requirements(data["order_id"], message.text, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении требований заказа. Повторите запрос позже"
        await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Требования заказа успешно изменены"
    await message.answer(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


@router.callback_query(F.data == "skip", EditOrderRequirements.requirements)
async def skip_requirements(callback: CallbackQuery, session: Any, state: FSMContext) -> None:
    """Запись требований пустыми"""
    # Получаем данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        await AsyncOrm.update_order_requirements(data["order_id"], None, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении требований заказа. Повторите запрос позже"
        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Требования заказа успешно изменены"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())


# ИЗМЕНЕНИЕ ФАЙЛОВ
@router.callback_query(and_f(F.data.split("|")[0] == "edit_order", F.data.split("|")[1] == "files"))
async def edit_files(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение файлов"""
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Меняем стейт
    await state.set_state(EditOrderFiles.files)

    # Заготовка для файлов
    await state.update_data(file_ids=[])
    await state.update_data(filenames=[])

    # Добавляем order_id в стейт
    order_id = int(callback.data.split("|")[2])
    await state.update_data(order_id=order_id)

    # Отправляем сообщение
    msg = "Отправьте <b>отдельными сообщениями</b> файлы (например с более подробным описанием ТЗ к задаче) или нажмите \"Оставить пустым\""
    await callback.answer()
    prev_mess = await callback.message.answer(msg, reply_markup=kb.cancel_skip_edit_order_keyboard(order_id).as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(EditOrderFiles.files)
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
            keyboard = kb.cancel_skip_edit_order_keyboard(data["order_id"])
        else:
            keyboard = kb.continue_cancel_keyboard(data["order_id"])

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
            keyboard = kb.cancel_skip_edit_order_keyboard(data["order_id"])
        else:
            keyboard = kb.continue_cancel_keyboard(data["order_id"])

        prev_mess = await message.answer("Размер файла не должен быть более 100МБ. Отправьте файл или нажмите \"Продолжить\"",
                                         reply_markup=keyboard.as_markup())
        # Сохраняем предыдущее сообщение
        await state.update_data(prev_mess=prev_mess)
        return

    # Проверяем если уже есть три файла
    if len(data["file_ids"]) == 3:
        prev_mess = await message.answer(
            "Вы уже отправили 3 файла, нажмите \"Продолжить\"",
            reply_markup=kb.continue_cancel_keyboard(data["order_id"]).as_markup()
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
    msg = f"Отправьте следующий файл или нажмите кнопку \"Продолжить\"\n\n" \
          f"Отправлено файлов {len(file_ids)}/3:\n{filenames_text}"
    prev_mess = await message.answer(msg, reply_markup=kb.continue_cancel_keyboard(data["order_id"]).as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(or_f(F.data == "continue", F.data == "skip"), EditOrderFiles.files)
async def get_files(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Обновление файлов"""
    # Получаем данные
    data = await state.get_data()

    # Очищаем стейт
    await state.clear()

    # Сохраняем информацию
    try:
        # Создаем схемы файлов
        files: List[TaskFileAdd] = []
        for idx in range(len(data["filenames"])):
            file = TaskFileAdd(file_id=data["file_ids"][idx], filename=data["filenames"][idx])
            files.append(file)

        await AsyncOrm.update_order_files(data["order_id"], files, session)
    except:
        msg = f"{btn.INFO} Ошибка при изменении файлов заказа. Повторите запрос позже"
        await callback.answer()
        await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())
        return

    # Отправляем сообщение
    msg = "✅ Файлы заказа успешно изменены"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=kb.to_order_keyboard(data["order_id"]).as_markup())