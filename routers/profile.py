from pathlib import Path

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.states.media import LoadMedia
from utils.s3_storage import save_file_to_s3_storage, get_file_from_s3_storage
from utils.download_files import load_photo_from_tg
from settings import settings

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


@router.message(Command(f"get"))
async def get_file_from_s3(message: types.Message) -> None:
    filename = f"{message.from_user.id}.jpg"

    await get_file_from_s3_storage(
        path=f"{settings.executors_profile_path}{filename}"
    )
    # для получения фото в формате для тг
    # photo = BufferedInputFile(file, filename="image")

    await message.answer(f"Фото успешно получено")


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



