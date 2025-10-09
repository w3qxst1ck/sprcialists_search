from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from middlewares.registered import RegisteredMiddleware
from middlewares.database import DatabaseMiddleware
from routers.states.media import LoadMedia

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


@router.callback_query(F.data == "add-photo")
async def add_photo_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(LoadMedia.photo)
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text=f"Отмена", callback_data="cancel-photo"))

    await callback.message.edit_text("Отправьте фотографию")


@router.message(LoadMedia.photo)
async def get_photo(message: types.Message, bot: Bot, state: FSMContext):
    # формируем путь для сохранения фото
    filename = str(message.from_user.id)
    filepath = f"{settings.profile_photo_path}/{filename}.jpg"

    try:
        # получаем фото
        photo = message.photo[-1]
        # скачиваем фото в локальную директорию
        await bot.download(photo.file_id, filepath)

        # save to s3
        await save_to_s3_storage(filepath, filename)

    except TypeError:
        await message.answer("Не удалось загрузить фотографию из вашего сообщения. "
                             "Пожалуйста, пришлите фотографию еще раз.")
        return

    await message.answer("Фото успешно загружено")
    await state.clear()


async def save_to_s3_storage(photo_path: str, filename: str):
    import boto3

    # Создаем клиент S3
    s3_client = boto3.client(
        's3',
        endpoint_url=settings.s3_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key
    )

    # Загружаем файл
    s3_client.upload_file(
        photo_path,
        "profile-media",
        filename
    )
    print(f"Фото {filename} успешно загружено!")


