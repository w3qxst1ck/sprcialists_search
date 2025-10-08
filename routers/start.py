from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.admin import AdminMiddleware
from routers.buttons import commands as cmd
from routers.keyboards.menu import main_menu_keyboard

from database.orm import AsyncOrm
from schemas.user import UserAdd
from database.tables import UserRoles

router = Router()
router.message.middleware.register(AdminMiddleware())
router.callback_query.middleware.register(AdminMiddleware())


@router.message(Command(f"{cmd.START[0]}"))
async def start(message: types.Message, admin: bool, session: any) -> None:
    """Старт хендлер"""
    tg_id = str(message.from_user.id)
    user_exists: bool = await AsyncOrm.check_user_already_exists(tg_id, session)

    # если пользователь зарегистрирован
    if user_exists:
        msg = "Главное меню"
        keyboard = main_menu_keyboard(admin)
        await message.answer(msg, reply_markup=keyboard.as_markup())
        return

    # первый запуск бота пользователем
    else:
        # создаем пользователя
        new_user = UserAdd(
            tg_id=tg_id,
            username=message.from_user.username,
            firstname=message.from_user.first_name,
            lastname=message.from_user.last_name,
            role=None
        )
        await AsyncOrm.create_user(new_user, session)

        keyboard = await choose_role_keyboard(message)
        msg = await get_start_message()
        await message.answer(msg, reply_markup=keyboard.as_markup())
        return


async def get_start_message() -> str:
    """Стартовое сообщение"""
    return "Привет! Это HIRE — бот для быстрого поиска проверенных креативных специалистов."


async def choose_role_keyboard(callback: CallbackQuery) -> InlineKeyboardBuilder:
    """Клавиатура выбора рли"""
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text=f"Я клиент", callback_data="choose_role|client"))
    keyboard.row(InlineKeyboardButton(text=f"Я исполнитель", callback_data="choose_role|executor"))
    keyboard.row(InlineKeyboardButton(text=f"ТЕст", callback_data="choose_role|test"))

    return keyboard


async def show_unregistered_message(event: CallbackQuery | Message, bot: Bot):
    await bot.send_message(event.from_user.id, "Вы еще не зарегистрированы")