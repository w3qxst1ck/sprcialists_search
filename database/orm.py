import datetime
from collections.abc import Mapping
from pydantic import ValidationError
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.tables import Base

from logger import logger
from schemas.user import UserAdd

# для model_validate регистрируем возвращаемый из asyncpg.fetchrow класс Record
Mapping.register(asyncpg.Record)


class AsyncOrm:

    @staticmethod
    async def create_tables():
        """Создание таблиц"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def drop_tables():
        """Удаление таблиц"""
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @staticmethod
    async def check_user_already_exists(tg_id: str, session: any) -> bool:
        """Проверка зарегистрирован ли пользователь"""
        try:
            exists = await session.fetchval(
                """
                SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = $1)
                """,
                tg_id)
            return exists
        except Exception as e:
            logger.error(f"Ошибка при проверке регистрации пользователя {tg_id}: {e}")

    @staticmethod
    async def create_user(user: UserAdd, session: Any) -> None:
        """Создание пользователя"""
        try:
            created_at = datetime.datetime.now()
            await session.execute(
                """
                INSERT INTO users (tg_id, username, firstname, lastname, role, created_at, is_banned, is_admin)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (tg_id) DO NOTHING
                """,
                user.tg_id, user.username, user.firstname, user.lastname, user.role, created_at, False, False
            )
            logger.info(f"Пользователь tg_id {user.tg_id} зарегистрировался")

        except Exception as e:
            logger.error(f"Ошибка при создании пользователя {user.tg_id} "
                         f"{'@' + user.username if user.username else ''}: {e}")

    @staticmethod
    async def user_has_role(tg_id: str, session: Any) -> bool:
        """Проверяет выбрана ли роль исполнитель/заказчик"""
        try:
            query = await session.fetchrow(
                """
                SELECT FROM users 
                WHERE tg_id = $1
                AND role IS NOT NULL
                """,
                tg_id
            )
            return query is not None

        except Exception as e:
            logger.error(f"Ошибка при проверки роли у пользователя {tg_id}: {e}")