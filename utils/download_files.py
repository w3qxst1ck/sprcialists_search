from aiogram import Bot, types

from settings import settings
from logger import logger


async def load_photo_from_tg(message: types.Message, bot: Bot, local_file_dir: str) -> str:
    """
        Загрузка фото из ТГ и сохранение в локальную директорию
        file_dir_type: str - передаем из settings
    """
    # Формируем путь для сохранения фото
    filename = f"{str(message.from_user.id)}.jpg"

    # Определяем директорию сохранения в зависимости от роли пользователя
    filepath = f"{settings.local_media_path}/{local_file_dir}/{filename}"

    try:
        # Получаем фото
        photo = message.photo[-1]
        # Скачиваем фото в локальную директорию
        await bot.download(photo.file_id, filepath)

    except Exception as e:
        logger.error(f"Ошибка при скачивании фото пользователя {message.from_user.id} из телеграмма {e}")
        raise

    return filename


