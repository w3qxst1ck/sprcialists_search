import datetime
from collections.abc import Mapping
from pydantic import ValidationError
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.tables import Base

from logger import logger
from schemas.profession import Profession, Job
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

    @staticmethod
    async def get_user_role(tg_id: str, session: Any) -> str | None:
        """Получение роли пользователя"""
        try:
            role = await session.fetchval(
                """
                SELECT role 
                FROM users
                WHERE tg_id = $1 
                """,
                tg_id
            )
            return role
        except Exception as e:
            logger.error(f"Ошибка при получении роли пользователя {tg_id}: {e}")

    @staticmethod
    async def get_professions(session: Any) -> List[Profession]:
        """Получение всех профессий"""
        try:
            rows = await session.fetch(
                """
                SELECT *
                FROM professions
                """
            )
            professions = [Profession.model_validate(row) for row in rows]
            return professions

        except Exception as e:
            logger.error(f"Ошибка при получении всех профессий: {e}")

    @staticmethod
    async def get_profession(profession_id: int, session: Any) -> Profession:
        """Получение профессии по id"""
        try:
            row = await session.fetchrow(
                """
                SELECT * 
                FROM professions
                WHERE id=$1 
                """,
                profession_id
            )
            return Profession.model_validate(row)

        except Exception as e:
            logger.error(f"Ошибка при получении профессии с id {profession_id}: {e}")

    @staticmethod
    async def get_jobs_by_profession(profession_id: int, session: Any) -> List[Job]:
        """Получение всех работ по выбранной профессии"""
        try:
            rows = await session.fetch(
                """
                SELECT *
                FROM jobs
                WHERE profession_id=$1
                """,
                profession_id
            )
            jobs = [Job.model_validate(row) for row in rows]
            return jobs

        except Exception as e:
            logger.error(f"Ошибка при получении всех jobs по профессии {profession_id}: {e}")

    @staticmethod
    async def get_jobs_by_ids(jobs_ids: List[int], session: Any) -> List[Job]:
        """Получение Jobs по списку id"""
        try:
            rows = await session.fetch(
                """
                SELECT * 
                FROM jobs
                WHERE id = ANY($1::int[])
                """,
                jobs_ids
            )
            jobs = [Job.model_validate(row) for row in rows]
            return jobs

        except Exception as e:
            logger.error(f"Ошибка при получении jobs с ids {jobs_ids}: {e}")
