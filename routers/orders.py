from typing import Any, List

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.orm import AsyncOrm
from middlewares.private import CheckPrivateMessageMiddleware
from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.states.orders import CreateOrder
from routers.keyboards import orders as kb
from schemas.profession import Profession

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())

router.message.middleware.register(CheckPrivateMessageMiddleware())
router.callback_query.middleware.register(CheckPrivateMessageMiddleware())


# СОЗДАНИЕ ЗАКАЗА
@router.callback_query(F.data == "create_order")
async def create_order_start(callback: CallbackQuery, state: FSMContext, session: Any) -> None:
    """Начало создания заказа"""
    # Устанавливаем стейт
    await state.set_state(CreateOrder.profession)

    # Получаем все профессии
    professions: List[Profession] = await AsyncOrm.get_professions(session)

    # Отправляем сообщение
    msg = "Выберите раздел для создания заказа"
    keyboard = kb.profession_keyboard(professions)
    prev_mess = await callback.message.edit_text(msg, reply_markup=keyboard.as_markup())

    # Сохраняем сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data.split("|")[0] == "choose_profession", CreateOrder.profession)
async def get_profession(callback: CallbackQuery, state: FSMContext) -> None:
    """Получение профессии, запрос названия"""
    # Записываем профессию
    profession_id = int(callback.data.split("|")[1])
    await state.update_data(profession_id=profession_id)

    # Меняем стейт
    await state.set_state(CreateOrder.title)

    # Запрашиваем название
    msg = "Отправьте название (заголовок) заказа"
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
    msg = "Отправьте краткое ТЗ"
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

    # Меняем стейт
    await state.set_state(CreateOrder.price)

    # Отправляем сообщение
    msg = "Отправьте цену заказа (например: 2000 рублей)"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.message(CreateOrder.price)
async def get_price(message: Message, state: FSMContext) -> None:
    """Получаем цену, запрашиваем дедлайн"""
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

    # Записываем ТЗ
    await state.update_data(price=message.text)

    # Меняем стейт
    await state.set_state(CreateOrder.deadline)

    # Отправляем сообщение
    msg = "Отправьте срок вашего заказа датой формата"
    prev_mess = await message.answer(msg, reply_markup=kb.cancel_keyboard().as_markup())

    # Сохраняем предыдущее сообщение
    await state.update_data(prev_mess=prev_mess)


@router.callback_query(F.data == "cancel_create_order", StateFilter("*"))
async def cancel_registration(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена создания заказа"""
    await state.clear()
    # TODO возвращать в мои заказы
    msg = "Отменено"

    try:
        await callback.message.edit_text(msg)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(msg)

