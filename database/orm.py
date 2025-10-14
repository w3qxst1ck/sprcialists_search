import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.tables import Base, UserRoles

from logger import logger
from schemas.client import ClientAdd, RejectReason, Client
from schemas.executor import ExecutorAdd
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

    @staticmethod
    async def create_executor(e: ExecutorAdd, session: Any) -> None:
        """Создание профиля исполнителя"""
        links = "|".join(e.links)
        langs = "|".join(e.langs)
        try:
            async with session.transaction():
                # Создание профиля исполнителя
                executor_id = await session.fetchval(
                    """
                    INSERT INTO executors (tg_id, name, age, description, rate, experience, links, availability, contacts, 
                    location, langs, photo, verified) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id
                    """,
                    e.tg_id, e.name, e.age, e.description, e.rate, e.experience, links, e.availability, e.contacts,
                    e.location, langs, e.photo, e.verified
                )

                # Создание связи ExecutorsJobs
                for job in e.jobs:
                    await session.execute(
                        """
                        INSERT INTO executors_jobs (job_id, executor_id)
                        VALUES ($1, $2)
                        """,
                        job.id, executor_id
                    )

                # Указываем роль у пользователя
                await session.execute(
                    """
                    UPDATE users
                    SET role = $1
                    WHERE tg_id = $2
                    """,
                    UserRoles.EXECUTOR.value, e.tg_id
                )
                logger.info(f"Создан профиль Исполнителя пользователем {e.tg_id}, id: {executor_id}")

        except Exception as ex:
            logger.error(f"Ошибка при создании профиля исполнителя пользователем {e.tg_id}: {ex}")

    @staticmethod
    async def create_client(client: ClientAdd, session: Any) -> None:
        """Запись в таблицу клиентов"""
        try:
            async with session.transaction():
                # Создаем профиль клиента
                client_id = await session.fetchval(
                    """
                    INSERT INTO clients (tg_id, name, description, type, links, langs, location, photo, verified)
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    client.tg_id, client.name, client.description, client.type.value, client.links, client.langs, client.location,
                    client.photo, client.verified
                )
                # Указываем роль у пользователя
                await session.execute(
                    """
                    UPDATE users
                    SET role = $1
                    WHERE tg_id = $2
                    """,
                    UserRoles.CLIENT.value, client.tg_id
                )

            logger.info(f"Создан профиль клиента пользователя {client.tg_id}, id: {client_id}")

        except Exception as e:
            logger.error(f"Ошибка при создании профиля клиента для пользователя {client.tg_id}: {e}")

    @staticmethod
    async def verify_executor(tg_id: str, admin_tg_id: str, session: Any) -> None:
        """Верификация исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET verified=True
                WHERE tg_id=$1
                """,
                tg_id
            )
            logger.info(f"Исполнитель {tg_id} верифицирован админом {admin_tg_id}")

        except Exception as e:
            logger.error(f"Ошибка при верификации исполнителя: {e}")

    @staticmethod
    async def verify_client(tg_id: str, admin_tg_id: str, session: Any) -> None:
        """Верификация клиента"""
        try:
            await session.execute(
                """
                UPDATE clients
                SET verified=True
                WHERE tg_id=$1
                """,
                tg_id
            )
            logger.info(f"Клиент {tg_id} верифицирован админом {admin_tg_id}")

        except Exception as e:
            logger.error(f"Ошибка при верификации клиента: {e}")

    @staticmethod
    async def get_reject_reasons(session: Any) -> list[RejectReason]:
        """Получение причин отказа"""
        try:
            rows = await session.fetch(
                """
                SELECT * FROM reject_reasons
                """
            )
            reasons: list[RejectReason] = [RejectReason.model_validate(row) for row in rows]
            return reasons

        except Exception as e:
            logger.error(f"Ошибка при получении причин отказа: {e}")

    @staticmethod
    async def get_reject_reason(reason_id: int, session: Any) -> RejectReason:
        """Получение причины отказа по id"""
        try:
            row = await session.fetchrow(
                """
                SELECT * FROM reject_reasons
                """
            )
            reason: RejectReason = RejectReason.model_validate(row)
            return reason

        except Exception as e:
            logger.error(f"Ошибка при получении причины отказа id {reason_id}: {e}")

    @staticmethod
    async def get_client(tg_id: str, session: Any) -> Client:
        """Получаем профиль клиента"""
        try:
            row = await session.fetchrow(
                """
                SELECT * FROM clients
                WHERE tg_id = $1
                """,
                tg_id
            )
            client: Client = Client.model_validate(row)
            return client

        except Exception as e:
            logger.error(f"Ошибка при получении профиля клиента у пользователя {tg_id}: {e}")
