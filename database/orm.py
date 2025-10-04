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
    async def create_user(user: UserAdd, session: Any) -> None:
        """Создание пользователя"""
        try:
            created_at = datetime.datetime.now()
            await session.execute("""
                INSERT INTO users (tg_id, username, firstname, lastname, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (tg_id) DO NOTHING
                """, user.tg_id, user.username, user.firstname, user.lastname, created_at)
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя {user.tg_id} "
                         f"{'@' + user.username if user.username else ''}: {e}")


