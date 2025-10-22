import os

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


async def load_cv_from_tg(message: types.Message, bot: Bot, local_file_dir: str) -> str:
    """
    Загрузка фото из ТГ и сохранение в локальную директорию
    file_dir_type: str - передаем из settings
    """
    # Формируем путь для сохранения файла
    filename = f"{str(message.from_user.id)}.pdf"

    # Определяем директорию сохранения в зависимости от роли пользователя
    filepath = f"{settings.local_media_path}{local_file_dir}{filename}"

    try:
        # Получаем фото
        file = message.document
        # Скачиваем фото в локальную директорию
        await bot.download(file.file_id, filepath)

    except Exception as e:
        logger.error(f"Ошибка при скачивании файла резюме пользователя {message.from_user.id} из телеграмма {e}")
        raise

    return filename


def get_photo_path(path: str, tg_id: str) -> str:
    """Получение пути в зависимости от роли"""
    return settings.local_media_path + path + f"{tg_id}.jpg"


def get_cv_path(path: str, tg_id: str) -> str:
    """Получение пути до резюме"""
    return settings.local_media_path + path + f"{tg_id}.pdf"


def check_cv_file(tg_id: str) -> bool:
    """Проверка наличия резюме файла"""
    cv_path = get_cv_path(settings.executors_cv_path, tg_id)
    cv_exists: bool = os.path.exists(cv_path)
    return cv_exists


