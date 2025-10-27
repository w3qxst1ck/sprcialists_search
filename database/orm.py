import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.tables import Base, UserRoles

from logger import logger
from schemas.client import ClientAdd, RejectReason, Client
from schemas.executor import ExecutorAdd, Executor
from schemas.order import OrderAdd, Order, TaskFile, TaskFileAdd
from schemas.profession import Profession, Job, ProfessionAdd
from schemas.user import UserAdd, User

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
    async def check_is_admin(tg_id: str, session: Any) -> bool:
        """Проверка является ли пользователь админом"""
        try:
            exists = await session.fetchval(
                """
                SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = $1 AND is_admin = true)
                """,
                tg_id
            )
            return exists
        except Exception as e:
            logger.error(f"Ошибка при проверке является ли пользователь {tg_id} админом: {e}")

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
    async def get_user(tg_id: str, session: Any) -> User | None:
        """Получение пользователя"""
        try:
            row = await session.fetchrow(
                """
                SELECT *
                FROM users
                WHERE tg_id=$1
                """,
                tg_id
            )
            if not row:
                return None
            return User.model_validate(row)

        except Exception as e:
            logger.error(f"Ошибка при получении пользователя tg_id {tg_id}: {e}")

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
    async def get_username(tg_id: str, session: Any) -> str | None:
        """Получение username"""
        try:
            username = await session.fetchval(
                """
                SELECT username
                FROM users
                WHERE tg_id = $1
                """,
                tg_id
            )
            return username
        except Exception as e:
            logger.error(f"Ошибка при получении username пользователя {tg_id}: {e}")

    @staticmethod
    async def update_username(tg_id: str, username: str, session: Any) -> None:
        """Обновление username пользователя"""
        try:
            await session.execute(
                """
                UPDATE users
                SET username = $1
                WHERE tg_id = $2
                """,
                username, tg_id
            )
            logger.info(f"Обновлено имя пользователя tg_id {tg_id} на {username}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении username пользователя {tg_id}: {e}")

    @staticmethod
    async def delete_user_role(tg_id: str, session: Any) -> None:
        """Удаление роли пользователя"""
        try:
            await session.execute(
                """
                UPDATE users
                SET role=null
                WHERE tg_id=$1
                """,
                tg_id
            )
            logger.info(f"Роль пользователя {tg_id} удалена")

        except Exception as e:
            logger.error(f"Ошибка при удалении роли пользователя {tg_id}: {e}")

    @staticmethod
    async def get_username(tg_id: str, session: Any) -> str:
        """Получение username по tg_id"""
        try:
            value = await session.fetchval(
                """
                SELECT username 
                FROM users
                WHERE tg_id = $1
                """,
                tg_id
            )
            return value

        except Exception as e:
            logger.error(f"Ошибка при получении username у user {tg_id}: {e}")

    @staticmethod
    async def create_profession(profession: ProfessionAdd, session: Any) -> None:
        """Создание профессии"""
        try:
            await session.execute(
                """
                INSERT INTO professions (title, emoji)
                VALUES ($1, $2)
                """,
                profession.title, profession.emoji
            )
            logger.info(f"Добавлена профессия {profession.emoji} {profession.title}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении профессии {profession.emoji} {profession.title}: {e}")
            raise

    @staticmethod
    async def update_profession(tg_id: str, jobs_ids: List[int], session: Any) -> None:
        """Изменение профессии и jobs у исполнителя"""
        try:
            async with session.transaction():
                # Получаем executor_id
                executor_id = await session.fetchval(
                    """
                    SELECT id
                    FROM executors
                    WHERE tg_id = $1
                    """,
                    tg_id
                )

                # Удаление старых записей из executor_jobs
                await session.execute(
                    """
                    DELETE FROM executors_jobs
                    WHERE executor_id = $1
                    """,
                    executor_id
                )

                # Создание связи ExecutorsJobs
                for job_id in jobs_ids:
                    await session.execute(
                        """
                        INSERT INTO executors_jobs (job_id, executor_id)
                        VALUES ($1, $2)
                        """,
                        job_id, executor_id
                    )
                logger.info(f"Профессии исполнителя tg_id {tg_id} изменены на {jobs_ids}")

        except Exception as e:
            logger.error(f"Ошибка при изменении профессий исполнителя tg_id {tg_id}: {e}")
            raise

    @staticmethod
    async def get_professions(session: Any) -> List[Profession]:
        """Получение всех профессий"""
        try:
            rows = await session.fetch(
                """
                SELECT *
                FROM professions
                ORDER BY title
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
                ORDER BY title
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
        updated_at = datetime.datetime.now()
        try:
            async with session.transaction():
                # Создание профиля исполнителя
                executor_id = await session.fetchval(
                    """
                    INSERT INTO executors (tg_id, name, age, description, rate, experience, links, availability, contacts, 
                    location, photo, verified) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                    """,
                    e.tg_id, e.name, e.age, e.description, e.rate, e.experience, links, e.availability, e.contacts,
                    e.location, e.photo, e.verified
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
                    SET role = $1, updated_at = $2
                    WHERE tg_id = $3
                    """,
                    UserRoles.EXECUTOR.value, updated_at, e.tg_id
                )

                logger.info(f"Создан профиль Исполнителя пользователем {e.tg_id}, id: {executor_id}")

        except Exception as ex:
            logger.error(f"Ошибка при создании профиля исполнителя пользователем {e.tg_id}: {ex}")
            raise

    @staticmethod
    async def delete_executor(tg_id: str, session: Any) -> None:
        """Удаление анкеты исполнителя"""
        try:
            await session.execute(
                """
                DELETE FROM executors
                WHERE tg_id=$1
                """,
                tg_id
            )
            logger.info(f"Анкета исполнителя пользователя {tg_id} удалена")

        except Exception as e:
            logger.error(f"Ошибка при удалении анкеты исполнителя пользователя {tg_id}: {e}")

    @staticmethod
    async def get_executor_by_tg_id(tg_id: str, session: Any) -> Executor | None:
        """Получение исполнителя по tg_id"""
        try:
            ex_row = await session.fetchrow(
                """
                SELECT id, tg_id, name, age, description, rate, experience, links, availability, contacts, location, 
                photo, verified
                FROM executors 
                WHERE tg_id = $1  
                """,
                tg_id
            )
            # Если не нашли исполнителя
            if not ex_row:
                return None

            jobs_rows = await session.fetch(
                """
                SELECT j.id, j.title, j.profession_id 
                FROM jobs AS j
                JOIN executors_jobs AS ej ON j.id = ej.job_id
                WHERE ej.executor_id = $1
                """,
                ex_row["id"]
            )

            jobs: list[Job] = []

            for job_row in jobs_rows:
                jobs.append(Job(id=job_row["id"], title=job_row["title"], profession_id=job_row["profession_id"]))

            prof_row = await session.fetchrow(
                """
                SELECT * FROM professions
                WHERE id = $1
                """,
                jobs[0].profession_id
            )
            profession = Profession.model_validate(prof_row)

            executor = Executor(
                id=ex_row["id"],
                tg_id=ex_row["tg_id"],
                name=ex_row["name"],
                age=ex_row["age"],
                description=ex_row["description"],
                rate=ex_row["rate"],
                experience=ex_row["experience"],
                links=ex_row["links"].split("|"),
                availability=ex_row["availability"],
                contacts=ex_row["contacts"],
                location=ex_row["location"],
                photo=ex_row["photo"],
                verified=ex_row["verified"],
                profession=profession,
                jobs=jobs
            )

            return executor

        except Exception as e:
            logger.error(f"Ошибка при получении профиля исполнителя пользователя tg_id {tg_id}: {e}")

    @staticmethod
    async def get_executor_name(tg_id: str, session: Any) -> str:
        """Получаем имя исполнителя по tg_id"""
        try:
            row = await session.fetchrow(
                """
                SELECT name FROM executors
                WHERE tg_id = $1
                """,
                tg_id
            )
            return row["name"]

        except Exception as e:
            logger.error(f"Ошибка при получении имени исполнителя с tg {tg_id}: {e}")

    @staticmethod
    async def update_rate(tg_id: str, rate: str, session: Any) -> None:
        """Изменение rate исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET rate = $1
                WHERE tg_id = $2
                """,
                rate, tg_id
            )
            logger.info(f"Ценовая информация исполнителя tg_id {tg_id} изменена на '{rate}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении ценовой информации исполнителя tg_id {tg_id} на '{rate}': {e}")
            raise

    @staticmethod
    async def update_experience(tg_id: str, experience: str, session: Any) -> None:
        """Изменение experience исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET experience = $1
                WHERE tg_id = $2
                """,
                experience, tg_id
            )
            logger.info(f"Опыт исполнителя tg_id {tg_id} изменен на '{experience}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении опыта исполнителя tg_id {tg_id} на '{experience}': {e}")
            raise

    @staticmethod
    async def update_description(tg_id: str, description: str, session: Any) -> None:
        """Изменение description исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET description = $1
                WHERE tg_id = $2
                """,
                description, tg_id
            )
            logger.info(f"Описание исполнителя tg_id {tg_id} изменено на '{description}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении описания исполнителя tg_id {tg_id} на '{description}': {e}")
            raise

    @staticmethod
    async def update_contacts(tg_id: str, contacts: str | None, session: Any) -> None:
        """Изменение contacts исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET contacts = $1
                WHERE tg_id = $2
                """,
                contacts, tg_id
            )
            logger.info(f"Контакты исполнителя tg_id {tg_id} изменены на '{contacts}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении контактов исполнителя tg_id {tg_id} на '{contacts}': {e}")
            raise

    @staticmethod
    async def update_location(tg_id: str, location: str | None, session: Any) -> None:
        """Изменение location исполнителя"""
        try:
            await session.execute(
                """
                UPDATE executors
                SET location = $1
                WHERE tg_id = $2
                """,
                location, tg_id
            )
            logger.info(f"Город исполнителя tg_id {tg_id} изменен на '{location}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении города исполнителя tg_id {tg_id} на '{location}': {e}")
            raise

    @staticmethod
    async def update_links(tg_id: str, links: List[str], session: Any) -> None:
        """Изменение ссылок на портфолио"""
        links = "|".join(links)
        try:
            await session.execute(
                """
                UPDATE executors
                SET links = $1
                WHERE tg_id = $2
                """,
                links, tg_id
            )
            logger.info(f"Ссылки на портфолио исполнителя tg_id {tg_id} изменены на '{links}'")
        except Exception as e:
            logger.error(f"Ошибка при изменении ссылок на портфолио исполнителя tg_id {tg_id} на '{links}': {e}")
            raise

    @staticmethod
    async def create_client(client: ClientAdd, session: Any) -> None:
        """Запись в таблицу клиентов"""
        updated_at = datetime.datetime.now()

        try:
            async with session.transaction():
                # Создаем профиль клиента
                client_id = await session.fetchval(
                    """
                    INSERT INTO clients (tg_id, name)
                    VALUES($1, $2)
                    RETURNING id
                    """,
                    client.tg_id, client.name
                )
                # Указываем роль у пользователя
                await session.execute(
                    """
                    UPDATE users
                    SET role = $1, updated_at = $2
                    WHERE tg_id = $3
                    """,
                    UserRoles.CLIENT.value, updated_at, client.tg_id
                )

            logger.info(f"Создан профиль клиента пользователя {client.tg_id}, id: {client_id}")

        except Exception as e:
            logger.error(f"Ошибка при создании профиля клиента для пользователя {client.tg_id}: {e}")
            raise

    @staticmethod
    async def delete_client(tg_id: str, session: Any) -> None:
        """Удаление анкеты клиента"""
        try:
            await session.execute(
                """
                DELETE FROM clients
                WHERE tg_id=$1
                """,
                tg_id
            )
            logger.info(f"Анкета клиента пользователя {tg_id} удалена")

        except Exception as e:
            logger.error(f"Ошибка при удалении анкеты клиента пользователя {tg_id}: {e}")

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
    async def is_verified(tg_id: str, session: Any):
        """true если анкета верифицирована, иначе false"""
        try:
            value = await session.fetchval(
                """
                SELECT verified FROM executors
                WHERE tg_id=$1
                """,
                tg_id
            )
            return value

        except Exception as e:
            logger.error(f"Ошибка при проверке верификации исполнителя {tg_id}: {e}")

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
    async def get_reject_reasons_by_ids(reasons_ids: List[int], session: Any) -> List[RejectReason]:
        """Получение причин отказа по id"""
        try:
            rows = await session.fetch(
                """
                SELECT * FROM reject_reasons
                WHERE id = ANY($1::int[])
                """,
                reasons_ids
            )
            reasons: list[RejectReason] = [RejectReason.model_validate(row) for row in rows]
            return reasons

        except Exception as e:
            logger.error(f"Ошибка при получении причин отказа по ids {reasons_ids}: {e}")

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

    @staticmethod
    async def get_client_id(tg_id: str, session) -> int:
        """Получение id пользователя по tg_id"""
        try:
            value = await session.fetchval(
                """
                SELECT id FROM clients 
                WHERE tg_id = $1
                """,
                tg_id
            )
            return value

        except Exception as e:
            logger.error(f"Ошибка при получении id клиента по tg_id {tg_id}: {e}")

    @staticmethod
    async def get_executor_id(tg_id: str, session: Any) -> int:
        """Получение id исполнителя по tg_id"""
        try:
            value = await session.fetchval(
                """
                SELECT id FROM executors 
                WHERE tg_id = $1
                """,
                tg_id
            )
            return value

        except Exception as e:
            logger.error(f"Ошибка при получении id исполнителя по tg_id {tg_id}: {e}")

    @staticmethod
    async def get_executors_by_jobs(jobs_ids: list[int], session: Any) -> list[Executor]:
        """Подбор исполнителей по jobs"""
        try:
            ex_rows = await session.fetch(
                """
                SELECT DISTINCT ex.id, ex.tg_id, ex.name, ex.age, ex.description, ex.rate, ex.experience, ex.links, 
                ex.availability, ex.contacts, ex.location, ex.photo, ex.verified  
                FROM executors as ex
                LEFT JOIN executors_jobs as ex_j ON ex.id = ex_j.executor_id 
                WHERE ex.verified=true AND ex_j.job_id = ANY($1::int[])
                """,
                jobs_ids
            )
            executors = []

            for ex_row in ex_rows:
                jobs_rows = await session.fetch(
                    """
                    SELECT j.id, j.title, j.profession_id 
                    FROM jobs AS j
                    JOIN executors_jobs AS ej ON j.id = ej.job_id
                    WHERE ej.executor_id = $1
                    """,
                    ex_row["id"]
                )

                jobs: list[Job] = []

                for job_row in jobs_rows:
                    jobs.append(
                        Job(
                            id=job_row["id"],
                            title=job_row["title"],
                            profession_id=job_row["profession_id"]
                        )
                    )

                prof_row = await session.fetchrow(
                    """
                    SELECT * FROM professions
                    WHERE id = $1
                    """,
                    jobs[0].profession_id
                )
                profession = Profession.model_validate(prof_row)

                executors.append(
                    Executor(
                        id=ex_row["id"],
                        tg_id=ex_row["tg_id"],
                        name=ex_row["name"],
                        age=ex_row["age"],
                        description=ex_row["description"],
                        rate=ex_row["rate"],
                        experience=ex_row["experience"],
                        links=ex_row["links"].split("|"),
                        availability=ex_row["availability"],
                        contacts=ex_row["contacts"],
                        location=ex_row["location"],
                        photo=ex_row["photo"],
                        verified=ex_row["verified"],
                        profession=profession,
                        jobs=jobs
                    )
                )

            return executors

        except Exception as e:
            logger.error(f"Ошибка при получении исполнителей для работ jobs_id {jobs_ids}: {e}")

    @staticmethod
    async def get_favorites_executors(client_tg_id: str, session: Any) -> list[Executor]:
        """Получаем избранным исполнителей для клиента"""
        try:
            ex_rows = await session.fetch(
                """
                SELECT DISTINCT ex.id, ex.tg_id, ex.name, ex.age, ex.description, ex.rate, ex.experience, ex.links, 
                ex.availability, ex.contacts, ex.location, ex.photo, ex.verified  
                FROM executors as ex
                LEFT JOIN favorite_executors AS f_ex ON ex.id = f_ex.executor_id
                LEFT JOIN clients AS c ON f_ex.client_id = c.id 
                WHERE ex.verified=true AND c.tg_id = $1  
                """,
                client_tg_id
            )

            executors = []
            for ex_row in ex_rows:
                jobs_rows = await session.fetch(
                    """
                    SELECT j.id, j.title, j.profession_id 
                    FROM jobs AS j
                    JOIN executors_jobs AS ej ON j.id = ej.job_id
                    WHERE ej.executor_id = $1
                    """,
                    ex_row["id"]
                )

                jobs: list[Job] = []

                for job_row in jobs_rows:
                    jobs.append(
                        Job(
                            id=job_row["id"],
                            title=job_row["title"],
                            profession_id=job_row["profession_id"]
                        )
                    )

                prof_row = await session.fetchrow(
                    """
                    SELECT * FROM professions
                    WHERE id = $1
                    """,
                    jobs[0].profession_id
                )
                profession = Profession.model_validate(prof_row)

                executors.append(
                    Executor(
                        id=ex_row["id"],
                        tg_id=ex_row["tg_id"],
                        name=ex_row["name"],
                        age=ex_row["age"],
                        description=ex_row["description"],
                        rate=ex_row["rate"],
                        experience=ex_row["experience"],
                        links=ex_row["links"].split("|"),
                        availability=ex_row["availability"],
                        contacts=ex_row["contacts"],
                        location=ex_row["location"],
                        photo=ex_row["photo"],
                        verified=ex_row["verified"],
                        profession=profession,
                        jobs=jobs
                    )
                )
            return executors

        except Exception as e:
            logger.error(f"Ошибка при получении избранных исполнителей для клиента {client_tg_id}: {e}")

    @staticmethod
    async def add_executor_to_favorite(client_id: int, executor_id: int, session: Any) -> None:
        """Добавляем исполнителя в список избранных для клиента"""
        try:
            await session.execute(
                """
                INSERT INTO favorite_executors (client_id, executor_id)
                VALUES ($1, $2)
                """,
                client_id, executor_id
            )

        except Exception as e:
            logger.error(f"Ошибка при добавлении исполнителя {executor_id} в список избранных клиента {client_id}")
            raise

    @staticmethod
    async def delete_executor_from_favorites(client_tg_id: str, executor_id: int, session: Any) -> None:
        """Удаляем исполнителя из favorites"""
        try:
            await session.execute(
                """
                DELETE FROM favorite_executors 
                WHERE client_id IN (
                    SELECT id FROM clients
                    WHERE tg_id = $1
                ) 
                AND executor_id = $2;
                """,
                client_tg_id, executor_id
            )

        except Exception as e:
            logger.error(f"Ошибка при удалении исполнителя {executor_id} из избранных клиента {client_tg_id}: {e}")
            raise

    @staticmethod
    async def executor_in_favorites(client_id: int, executor_id: int, session: Any) -> bool:
        """Получаем true если исполнитель уже в списке избранных, иначе false"""
        try:
            row = await session.fetchrow(
                """
                SELECT * FROM favorite_executors
                WHERE client_id = $1 AND executor_id = $2
                """,
                client_id, executor_id
            )
            return True if row else False

        except Exception as e:
            logger.error(f"Ошибка при проверке исполнителя {executor_id} в списке избранных клиента {client_id}: {e}")

    @staticmethod
    async def create_order(order: OrderAdd, session: Any) -> None:
        """Создание заказа"""
        try:
            async with session.transaction():
                # Создание записи в таблице orders
                order_id = await session.fetchval(
                    """
                    INSERT INTO orders (title, task, price, requirements, period, created_at, client_id, tg_id, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    order.title, order.task, order.price, order.requirements, order.period, order.created_at,
                    order.client_id, order.tg_id, order.is_active
                )

                # Создаем записи в таблице orders_jobs
                for job in order.jobs:
                    await session.execute(
                        """
                        INSERT INTO orders_jobs (order_id, job_id)
                        VALUES ($1, $2)
                        """,
                        order_id, job.id
                    )

                # Создаем записи в таблице taskfiles
                for file in order.files:
                    await session.execute(
                        """
                        INSERT INTO taskfiles (filename, file_id, order_id)
                        VALUES ($1, $2, $3)
                        """,
                        file.filename, file.file_id, order_id
                    )

                logger.info(f"Создан заказ id {order_id} пользователем {order.tg_id}, client_id {order.client_id}")

        except Exception as e:
            logger.error(f"Ошибка при создании заказа пользователем {order.tg_id}, client_id: {order.client_id}: {e}")
            raise

    @staticmethod
    async def get_orders_by_client(tg_id: str, session: Any) -> List[Order]:
        """Получение заказов клиента"""
        try:
            orders = []

            order_rows = await session.fetch(
                """
                SELECT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                FROM orders AS o
                WHERE o.tg_id = $1
                ORDER BY created_at
                """,
                tg_id
            )

            for order_row in order_rows:
                # получаем jobs для заказа
                jobs_rows = await session.fetch(
                    """
                    SELECT j.id, j.title, j.profession_id
                    FROM jobs AS j
                    JOIN orders_jobs AS oj ON j.id = oj.job_id
                    WHERE oj.order_id = $1
                    """,
                    order_row["id"]
                )
                jobs: List[Job] = [Job.model_validate(job_row) for job_row in jobs_rows]

                # Получаем profession для заказа
                profession_row = await session.fetchrow(
                    """
                    SELECT * 
                    FROM professions
                    WHERE id = $1 
                    """,
                    jobs[0].profession_id
                )
                profession: Profession = Profession.model_validate(profession_row)

                # Получаем файлы для заказа
                files_rows = await session.fetch(
                    """
                        SELECT *
                        FROM taskfiles
                        WHERE order_id=$1
                    """,
                    order_row["id"]
                )
                files: List[TaskFile] = [TaskFile.model_validate(file_row) for file_row in files_rows]

                # Модель заказа
                order = Order(
                    id=order_row["id"],
                    client_id=order_row["client_id"],
                    tg_id=order_row["tg_id"],
                    profession=profession,
                    jobs=jobs,
                    title=order_row["title"],
                    task=order_row["task"],
                    price=order_row["price"],
                    period=order_row["period"],
                    requirements=order_row["requirements"],
                    created_at=order_row["created_at"],
                    is_active=order_row["is_active"],
                    files=files
                )
                orders.append(order)

            return orders

        except Exception as e:
            logger.error(f"Ошибка при получении заказов клиента {tg_id}: {e}")

    @staticmethod
    async def get_order_by_id(order_id: int, session: Any) -> Order:
        """Получение заказа по id"""
        try:
            # Получаем заказ
            order_row = await session.fetchrow(
                """
                SELECT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                FROM orders AS o
                WHERE o.id = $1
                """,
                order_id
            )

            # Получаем jobs для заказа
            jobs_rows = await session.fetch(
                """
                SELECT j.id, j.title, j.profession_id
                FROM jobs AS j
                JOIN orders_jobs AS oj ON j.id = oj.job_id
                WHERE oj.order_id = $1
                """,
                order_id
            )
            jobs: List[Job] = [Job.model_validate(job_row) for job_row in jobs_rows]

            # Получаем profession для заказа
            profession_row = await session.fetchrow(
                """
                SELECT * 
                FROM professions
                WHERE id = $1 
                """,
                jobs[0].profession_id
            )
            profession: Profession = Profession.model_validate(profession_row)

            # Получаем файлы для заказа
            files_rows = await session.fetch(
                """
                SELECT *
                FROM taskfiles
                WHERE order_id=$1
                """,
                order_id
            )
            files: List[TaskFile] = [TaskFile.model_validate(file_row) for file_row in files_rows]

            # Модель заказа
            order = Order(
                id=order_id,
                client_id=order_row["client_id"],
                tg_id=order_row["tg_id"],
                profession=profession,
                jobs=jobs,
                title=order_row["title"],
                task=order_row["task"],
                price=order_row["price"],
                period=order_row["period"],
                requirements=order_row["requirements"],
                created_at=order_row["created_at"],
                is_active=order_row["is_active"],
                files=files,
            )
            return order

        except Exception as e:
            logger.error(f"Ошибка при получении заказа id {order_id}: {e}")

    @staticmethod
    async def delete_order(order_id: int, session: Any) -> None:
        """Удаление заказа"""
        try:
            await session.execute(
                """
                DELETE FROM orders
                WHERE id=$1
                """,
                order_id
            )
            logger.info(f"Заказ id {order_id} удален")

        except Exception as e:
            logger.error(f"Ошибка при удалении заказа id {order_id}: {e}")

    @staticmethod
    async def get_orders_by_jobs(jobs_ids: list[int], session: Any, only_active: bool = True) -> list[Order]:
        """Получение списка заказов по jobs_id"""
        try:
            orders = []

            if only_active:
                order_rows = await session.fetch(
                    """
                    SELECT DISTINCT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                    FROM orders AS o
                    JOIN orders_jobs AS oj ON o.id = oj.order_id
                    WHERE oj.job_id = ANY($1::int[]) AND o.is_active = true
                    """,
                    jobs_ids
                )
            else:
                order_rows = await session.fetch(
                    """
                    SELECT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                    FROM orders AS o
                    JOIN orders_jobs AS oj ON o.id = oj.order_id
                    WHERE oj.job_id = ANY($1::int[])
                    """,
                    jobs_ids
                )

            for order_row in order_rows:
                # получаем jobs для заказа
                jobs_rows = await session.fetch(
                    """
                    SELECT j.id, j.title, j.profession_id
                    FROM jobs AS j
                    JOIN orders_jobs AS oj ON j.id = oj.job_id
                    WHERE oj.order_id = $1
                    """,
                    order_row["id"]
                )
                jobs: List[Job] = [Job.model_validate(job_row) for job_row in jobs_rows]

                # Получаем profession для заказа
                profession_row = await session.fetchrow(
                    """
                    SELECT * 
                    FROM professions
                    WHERE id = $1 
                    """,
                    jobs[0].profession_id
                )
                profession: Profession = Profession.model_validate(profession_row)

                # Получаем файлы для заказа
                files_rows = await session.fetch(
                    """
                        SELECT *
                        FROM taskfiles
                        WHERE order_id=$1
                    """,
                    order_row["id"]
                )
                files: List[TaskFile] = [TaskFile.model_validate(file_row) for file_row in files_rows]

                # Модель заказа
                order = Order(
                    id=order_row["id"],
                    client_id=order_row["client_id"],
                    tg_id=order_row["tg_id"],
                    profession=profession,
                    jobs=jobs,
                    title=order_row["title"],
                    task=order_row["task"],
                    price=order_row["price"],
                    period=order_row["period"],
                    requirements=order_row["requirements"],
                    created_at=order_row["created_at"],
                    is_active=order_row["is_active"],
                    files=files
                )
                orders.append(order)

            return orders

        except Exception as e:
            logger.error(f"Ошибка при получении заказов для jobs id {jobs_ids}: {e}")

    @staticmethod
    async def update_order_profession(order_id: int, jobs_ids: List[int], session) -> None:
        """Изменение профессии заказа"""
        try:
            async with session.transaction():
                # Удаление старых записей из orders_jobs
                await session.execute(
                    """
                    DELETE FROM orders_jobs
                    WHERE order_id = $1
                    """,
                    order_id)

                # Создание связи OrdersJobs
                for job_id in jobs_ids:
                    await session.execute(
                        """
                        INSERT INTO orders_jobs (job_id, order_id)
                        VALUES ($1, $2)
                        """,
                        job_id, order_id
                    )
                logger.info(f"Профессии заказа id {order_id} изменены на {jobs_ids}")

        except Exception as e:
            logger.error(f"Ошибка при изменении профессий заказа id {order_id}: {e}")
            raise

    @staticmethod
    async def update_order_title(order_id: int, title: str, session: Any) -> None:
        """Изменение названия заказа"""
        try:
            await session.execute(
                """
                UPDATE orders
                SET title = $1
                WHERE id = $2
                """,
                title, order_id
            )
            logger.info(f"Название заказа id {order_id} изменено на '{title}'")

        except Exception as e:
            logger.error(f"Ошибка при изменении названия заказа id {order_id} на '{title}': {e}")
            raise

    @staticmethod
    async def update_order_task(order_id: int, task: str, session: Any) -> None:
        """Изменение ТЗ заказа"""
        try:
            await session.execute(
                """
                UPDATE orders
                SET task = $1
                WHERE id = $2
                """,
                task, order_id
            )
            logger.info(f"ТЗ заказа id {order_id} изменено на '{task}'")

        except Exception as e:
            logger.error(f"Ошибка при изменении ТЗ заказа id {order_id} на '{task}': {e}")
            raise

    @staticmethod
    async def update_order_price(order_id: int, price: str | None, session: Any) -> None:
        """Изменение цены заказа"""
        try:
            await session.execute(
                """
                UPDATE orders
                SET price = $1
                WHERE id = $2
                """,
                price, order_id
            )
            logger.info(f"Цена заказа id {order_id} изменена на {price}")

        except Exception as e:
            logger.error(f"Ошибка при изменении цены заказа id {order_id} на {price}: {e}")
            raise

    @staticmethod
    async def update_order_period(order_id: int, period: int, session: Any) -> None:
        """Изменение срока заказа"""
        try:
            await session.execute(
                """
                UPDATE orders
                SET period = $1
                WHERE id = $2
                """,
                period, order_id
            )
            logger.info(f"Срок заказа id {order_id} изменена на {period}")

        except Exception as e:
            logger.error(f"Ошибка при изменении срока заказа id {order_id} на {period}: {e}")
            raise

    @staticmethod
    async def update_order_requirements(order_id: int, reqs: str | None, session: Any) -> None:
        """Изменение требований заказа"""
        try:
            await session.execute(
                """
                UPDATE orders
                SET requirements = $1
                WHERE id = $2
                """,
                reqs, order_id
            )
            logger.info(f"Требования заказа id {order_id} изменены на '{reqs}'")

        except Exception as e:
            logger.error(f"Ошибка при изменении требований заказа id {order_id} на '{reqs}': {e}")
            raise

    @staticmethod
    async def update_order_files(order_id: int, files: List[TaskFileAdd], session) -> None:
        """Изменение файлов заказа"""
        # Если есть файлы
        if files:
            try:
                async with session.transaction():
                    # Удаление старых записей из taskfiles
                    await session.execute(
                        """
                        DELETE FROM taskfiles
                        WHERE order_id = $1
                        """,
                        order_id
                    )

                    # Создание taskfiles
                    for file in files:
                        await session.execute(
                            """
                            INSERT INTO taskfiles (filename, file_id, order_id)
                            VALUES ($1, $2, $3)
                            """,
                            file.filename, file.file_id, order_id
                        )
                    files_text = ', '.join([f.filename for f in files])
                    logger.info(f"Файлы заказа id {order_id} изменены на {files_text}")

            except Exception as e:
                files_text = ', '.join([f.filename for f in files])
                logger.error(f"Ошибка при изменении файлов заказа id {files_text}: {e}")
                raise

        # Если оставили пустым
        else:
            try:
                # Удаление старых записей из taskfiles
                await session.execute(
                    """
                    DELETE FROM taskfiles
                    WHERE order_id = $1
                    """,
                    order_id
                )
                logger.info(f"Файлы заказа id {order_id} удалены")

            except Exception as e:
                logger.error(f"Ошибка при удалении файлов заказа id {order_id}: {e}")
                raise

    @staticmethod
    async def add_order_to_favorites(executor_id: int, order_id: int, session: Any):
        """Добавление заказа в избранное"""
        try:
            await session.execute(
                """
                INSERT INTO favorite_orders(executor_id, order_id)
                VALUES($1, $2)
                """,
                executor_id, order_id
            )

        except Exception as e:
            logger.error(f"Ошибка при добавлении заказа {order_id} для исполнителя {executor_id}: {e}")
            raise

    @staticmethod
    async def is_order_already_in_favorites(executor_tg_id: str, order_id: int, session: Any) -> bool:
        """True если заказ уже есть в избранном у исполнителя, иначе false"""
        try:
            query = await session.fetchrow(
                """
                SELECT FROM favorite_orders AS fav_or
                JOIN executors AS ex ON fav_or.executor_id  = ex.id
                WHERE ex.tg_id = $1 AND fav_or.order_id = $2
                """,
                executor_tg_id, order_id
            )
            return query is not None

        except Exception as e:
            logger.error(f"Ошибка при проверке заказа  {order_id} в избранном  для исполнителя {executor_tg_id}: {e}")

    @staticmethod
    async def get_favorites_orders(executor_id: int, session: Any, only_active: bool = True) -> list[Order]:
        """Получаем избранные заказы для исполнителя"""
        try:
            orders = []

            if only_active:
                order_rows = await session.fetch(
                    """
                    SELECT DISTINCT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                    FROM orders AS o
                    JOIN favorite_orders AS fav_o ON o.id = fav_o.order_id
                    WHERE o.is_active = true AND fav_o.executor_id = $1 
                    """,
                    executor_id
                )
            else:
                order_rows = await session.fetch(
                    """
                    SELECT o.id, o.title, o.task, o.price, o.requirements, o.period, o.created_at, o.client_id, o.tg_id, o.is_active 
                    FROM orders AS o
                    JOIN orders_jobs AS oj ON o.id = oj.order_id
                    JOIN favorite_orders AS fav_o ON o.id = fav_o.order_id
                    WHERE fav_o.executor_id = $1 
                    """,
                    executor_id
                )

            for order_row in order_rows:
                # получаем jobs для заказа
                jobs_rows = await session.fetch(
                    """
                    SELECT j.id, j.title, j.profession_id
                    FROM jobs AS j
                    JOIN orders_jobs AS oj ON j.id = oj.job_id
                    WHERE oj.order_id = $1
                    """,
                    order_row["id"]
                )
                jobs: List[Job] = [Job.model_validate(job_row) for job_row in jobs_rows]

                # Получаем profession для заказа
                profession_row = await session.fetchrow(
                    """
                    SELECT * 
                    FROM professions
                    WHERE id = $1 
                    """,
                    jobs[0].profession_id
                )
                profession: Profession = Profession.model_validate(profession_row)

                # Получаем файлы для заказа
                files_rows = await session.fetch(
                    """
                        SELECT *
                        FROM taskfiles
                        WHERE order_id=$1
                    """,
                    order_row["id"]
                )
                files: List[TaskFile] = [TaskFile.model_validate(file_row) for file_row in files_rows]

                # Модель заказа
                order = Order(
                    id=order_row["id"],
                    client_id=order_row["client_id"],
                    tg_id=order_row["tg_id"],
                    profession=profession,
                    jobs=jobs,
                    title=order_row["title"],
                    task=order_row["task"],
                    price=order_row["price"],
                    period=order_row["period"],
                    requirements=order_row["requirements"],
                    created_at=order_row["created_at"],
                    is_active=order_row["is_active"],
                    files=files
                )
                orders.append(order)

            return orders

        except Exception as e:
            logger.error(f"Ошибка при получении избранных заказов исполнителя {executor_id}: {e}")

    @staticmethod
    async def delete_order_from_favorites(executor_tg_id: str, order_id: int, session: Any) -> None:
        """Удаление заказа из списка избранных"""
        try:
            await session.execute(
                """
                DELETE FROM favorite_orders 
                WHERE executor_id IN (
                    SELECT id FROM executors
                    WHERE tg_id = $1
                ) 
                AND order_id = $2;
                """,
                executor_tg_id, order_id
            )

        except Exception as e:
            logger.error(f"Ошибка при удалении заказа {order_id} из избранных исполнителя {executor_tg_id}: {e}")
            raise

