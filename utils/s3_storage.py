import os
from pathlib import Path

import boto3

from settings import settings
from logger import logger


async def save_file_to_s3_storage(filename: str, local_file_dir: str = "profiles/executors"):
    """Загрузка файла в s3 хранилище"""
    # Формируем локальный путь до имеющегося файла
    local_dir_path = f"{settings.local_media_path}/{local_file_dir}/{filename}"

    # Определяем в какую папку необходимо загрузить файл
    s3_bucket_upload_dir = f"{local_file_dir}/{filename}"

    try:
        # Создаем клиент S3
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key
        )

        # Загружаем файл
        s3_client.upload_file(
            local_dir_path,
            settings.s3_bucket_name,
            s3_bucket_upload_dir
        )

    except Exception as e:
        logger.error(f"Ошибка при сохранении файла \"{filename}\" путь {local_dir_path} в s3 хранилище: {e}")
        raise


async def get_file_from_s3_storage(path: str) -> bytes:
    """Загрузка файла из s3 хранилища в локальную папку"""
    try:
        # Получаем путь до корня проекта
        project_dir = Path(__file__).parent.parent

        # Формируем путь до сохраняемого файла
        local_file_path = f"{project_dir}/{settings.local_media_path}{path}"

        # Создаем клиент S3
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key
        )

        # Получаем файл
        response = s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=path
        )
        binary_data: bytes = response['Body'].read()

        # Сохраняем файл в локальную директорию
        with open(local_file_path, 'wb') as f:
            f.write(binary_data)

        return binary_data

    except Exception as e:
        logger.error(f"Ошибка при загрузке файла \"{path}\" из s3 хранилища: {e}")
        raise
