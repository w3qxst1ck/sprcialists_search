import datetime
from collections.abc import Mapping
from typing import Any, List

import asyncpg

from database.database import async_engine
from database.tables import Base, UserRoles

from logger import logger
from schemas.client import ClientAdd, RejectReason, Client
from schemas.executor import ExecutorAdd, Executor
from schemas.order import OrderAdd, Order, TaskFile
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
            updated_at = datetime.datetime.now()
            await session.execute(
                """
                INSERT INTO users (tg_id, username, firstname, lastname, role, created_at, updated_at, is_banned, is_admin)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (tg_id) DO NOTHING
                """,
                user.tg_id, user.username, user.firstname, user.lastname, user.role, created_at, updated_at, False, False
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
        langs = "|".join(e.langs)
        updated_at = datetime.datetime.now()
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
                SELECT id from clients 
                WHERE tg_id = $1
                """,
                tg_id
            )
            return value
        except Exception as e:
            logger.error(f"Ошибка при получении id пользователя по tg_id {tg_id}: {e}")

    @staticmethod
    async def get_executors_by_jobs(jobs_ids: list[int], session: Any) -> list[Executor]:
        """Подбор исполнителей по jobs"""
        try:
            ex_rows = await session.fetch(
                """
                SELECT DISTINCT ex.id, ex.tg_id, ex.name, ex.age, ex.description, ex.rate, ex.experience, ex.links, 
                ex.availability, ex.contacts, ex.location, ex.langs, ex.photo, ex.verified  
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
                        langs=ex_row["langs"].split("|"),
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
                ex.availability, ex.contacts, ex.location, ex.langs, ex.photo, ex.verified  
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
                        langs=ex_row["langs"].split("|"),
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
                    INSERT INTO orders (title, task, price, requirements, deadline, created_at, client_id, tg_id, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    order.title, order.task, order.price, order.requirements, order.deadline, order.created_at,
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
                SELECT o.id, o.title, o.task, o.price, o.requirements, o.deadline, o.created_at, o.client_id, o.tg_id, o.is_active 
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
                    deadline=order_row["deadline"],
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
                SELECT o.id, o.title, o.task, o.price, o.requirements, o.deadline, o.created_at, o.client_id, o.tg_id, o.is_active 
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
                deadline=order_row["deadline"],
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