from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.states.media import LoadMedia
from utils.s3_storage import save_file_to_s3_storage
from utils.download_files import load_photo_from_tg

router = Router()

router.message.middleware.register(DatabaseMiddleware())
router.callback_query.middleware.register(DatabaseMiddleware())

router.message.middleware.register(RegisteredMiddleware())
router.callback_query.middleware.register(RegisteredMiddleware())


@router.callback_query(F.data.split("|")[1] == "test")
async def test_handler(callback: CallbackQuery):
    await callback.message.answer("Все норм вы зарегистрированы")


@router.message(Command(f"tester"))
async def start(message: types.Message) -> None:
    """Старт хендлер"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"Добавить фото", callback_data="add-photo"))

    await message.answer("выберите действие", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "add-photo")
async def add_photo_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LoadMedia.photo)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"Отмена", callback_data="cancel-photo"))

    await callback.message.edit_text("Отправьте фотографию")


@router.message(LoadMedia.photo)
async def get_photo(message: types.Message, bot: Bot, state: FSMContext):
    try:
        filename: str = await load_photo_from_tg(message, bot)
        await save_file_to_s3_storage(filename)

    except Exception:
        await message.answer(f"Не удалось загрузить фото, попробуйте еще раз")
        return

    await message.answer("Фото успешно загружено")
    await state.clear()



