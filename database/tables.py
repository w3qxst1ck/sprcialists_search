import datetime
from enum import Enum

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, String


class ClientType(Enum):
    INDIVIDUAL = "частное лицо"
    STUDIO = "студия"
    COMPANY = "компания"


class Availability(Enum):
    FREE = "свободен"
    BUSY = "в работе"
    HALF_BUSY = "занят частично"


class UserRoles(Enum):
    CLIENT = "клиент"
    EXECUTOR = "исполнитель"


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(index=True, unique=True)
    username: Mapped[str] = mapped_column(nullable=True)
    firstname: Mapped[str] = mapped_column(nullable=True)
    lastname: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime]
    updated_at: Mapped[datetime.datetime]
    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    role: Mapped[UserRoles] = mapped_column(String, index=True, nullable=True)

    executor_profile: Mapped["Executors"] = relationship(uselist=False, back_populates="user")
    client_profile: Mapped["Clients"] = relationship(uselist=False, back_populates="user")


class Clients(Base):
    """Таблица с полями профиля клиента"""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Имя пользователя должно содержать не более 50 символов")

    user: Mapped["User"] = relationship(back_populates="client_profile")
    orders: Mapped[list["Orders"]] = relationship(back_populates="client")
    favorites: Mapped[list["Executors"]] = relationship(back_populates="clients", secondary="favorite_executors")


class Executors(Base):
    """Таблица с полями профиля исполнителя"""
    __tablename__ = "executors"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Имя пользователя должно содержать не более 50 символов")
    age: Mapped[int] = mapped_column(nullable=True, default=None)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rate: Mapped[str] = mapped_column(nullable=False)
    experience: Mapped[str] = mapped_column(nullable=False)
    links: Mapped[str] = mapped_column(nullable=False)
    availability: Mapped[Availability] = mapped_column(String, default=Availability.FREE, nullable=False)
    contacts: Mapped[str] = mapped_column(nullable=True, default=None)
    location: Mapped[str] = mapped_column(nullable=True, default=None)
    photo: Mapped[bool] = mapped_column(nullable=False, default=False)
    verified: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="executor_profile")

    jobs: Mapped[list["Jobs"]] = relationship(back_populates="executors", secondary="executors_jobs")
    favorites: Mapped[list["Clients"]] = relationship(back_populates="executors", secondary="favorite_executors")


class Professions(Base):
    """Список профессий"""
    __tablename__ = "professions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False, index=True, unique=True)
    emoji: Mapped[str] = mapped_column(nullable=True)

    jobs: Mapped[list["Jobs"]] = relationship(back_populates="profession")


class Jobs(Base):
    """Выполняемые работы в профессии"""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False, index=True, unique=True)

    profession_id: Mapped[int] = mapped_column(ForeignKey("professions.id", ondelete="CASCADE"))
    executors: Mapped[list["Executors"]] = relationship(back_populates="jobs", secondary="executors_jobs")
    orders: Mapped[list["Orders"]] = relationship(back_populates="jobs", secondary="orders_jobs")


class ExecutorsJobs(Base):
    """
        Связь пользователя (исполнителя) с профессией и выполняемыми работами
        Many-to-many relationship
    """
    __tablename__ = "executors_jobs"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"), primary_key=True)


class RejectReasons(Base):
    """Ответы для отклоненных заявок на регистрацию"""
    __tablename__ = "reject_reasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    reason: Mapped[str] = mapped_column(index=True, nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)


class Orders(Base):
    """Заказы размещаемые клиентами"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    task: Mapped[str] = mapped_column(String(1000), nullable=False)
    price: Mapped[str] = mapped_column(nullable=True)
    requirements: Mapped[str] = mapped_column(nullable=True)
    period: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime]
    is_active: Mapped[bool] = mapped_column(nullable=False)

    client_id: Mapped[int] = mapped_column(ForeignKey("professions.id", ondelete="CASCADE"))
    jobs: Mapped[list["Jobs"]] = relationship(back_populates="orders", secondary="orders_jobs")
    files: Mapped[list["TaskFiles"]] = relationship(back_populates="order")


class FavoriteExecutors(Base):
    """Many-to-many таблица для хранения избранных исполнителей для клиентов"""
    __tablename__ = "favorite_executors"

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"), primary_key=True)


class OrdersJobs(Base):
    """
        Связь заказа с профессией и выполняемыми работами
        Many-to-many relationship
    """
    __tablename__ = "orders_jobs"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)


class TaskFiles(Base):
    """Файлы прикрепленные к заказам"""
    __tablename__ = "taskfiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(nullable=False)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))