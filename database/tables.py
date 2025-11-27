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
    BUSY = "занят"


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
    updated_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    role: Mapped[UserRoles] = mapped_column(String, index=True, nullable=True)

    executor_profile: Mapped["Executors"] = relationship(uselist=False, back_populates="user")
    client_profile: Mapped["Clients"] = relationship(uselist=False, back_populates="user")
    blocked: Mapped["BlockedUsers"] = relationship(uselist=False, back_populates="user")

    def __str__(self):
        return f"id {self.id}. {self.tg_id} {self.username + ' ' if self.username else ''}"


class Clients(Base):
    """Таблица с полями профиля клиента"""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Имя пользователя должно содержать не более 50 символов")
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="client_profile")

    orders: Mapped[list["Orders"]] = relationship(back_populates="client")

    views: Mapped[list["ExecutorsViews"]] = relationship(back_populates="client")

    # favorites: Mapped[list["Executors"]] = relationship(back_populates="clients", secondary="favorite_executors")
    executors_favorites: Mapped[list["Executors"]] = relationship(
        secondary="favorite_executors",
        back_populates="clients_favorites"
    )

    def __str__(self):
        return f"заказчик {self.name}"


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
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="executor_profile")

    jobs: Mapped[list["Jobs"]] = relationship(back_populates="executors", secondary="executors_jobs")

    responses: Mapped[list["OrdersResponses"]] = relationship(back_populates="executor", cascade="all, delete")

    views: Mapped[list["ExecutorsViews"]] = relationship(back_populates="executor", cascade="all, delete")

    clients_favorites: Mapped[list["Clients"]] = relationship(
        secondary="favorite_executors",
        back_populates="executors_favorites"
    )
    orders_favorites: Mapped[list["Orders"]] = relationship(
        secondary="favorite_orders",
        back_populates="executors_favorites"
    )

    def __str__(self):
        return f"исполнитель {self.name}"


class Professions(Base):
    """Список профессий"""
    __tablename__ = "professions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False, index=True, unique=True)
    emoji: Mapped[str] = mapped_column(nullable=True)

    jobs: Mapped[list["Jobs"]] = relationship(back_populates="profession", cascade="all, delete")

    def __str__(self):
        return f"{self.title}"


class Jobs(Base):
    """Выполняемые работы в профессии"""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False, index=True)

    profession_id: Mapped[int] = mapped_column(ForeignKey("professions.id", ondelete="CASCADE"))
    profession: Mapped["Professions"] = relationship(back_populates="jobs")
    executors: Mapped[list["Executors"]] = relationship(back_populates="jobs", secondary="executors_jobs")
    orders: Mapped[list["Orders"]] = relationship(back_populates="jobs", secondary="orders_jobs")

    def __str__(self):
        return f"{self.title}"


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
    period: Mapped[int] = mapped_column(nullable=False)


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

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    client: Mapped["Clients"] = relationship(back_populates="orders")

    jobs: Mapped[list["Jobs"]] = relationship(back_populates="orders", secondary="orders_jobs")

    files: Mapped[list["TaskFiles"]] = relationship(back_populates="order")

    responses: Mapped[list["OrdersResponses"]] = relationship(back_populates="order", cascade="all, delete")

    executors_favorites: Mapped[list["Executors"]] = relationship(
        secondary="favorite_orders",
        back_populates="orders_favorites"
    )

    def __str__(self):
        return f"{self.title} {self.price}"


class FavoriteExecutors(Base):
    """Many-to-many таблица для хранения избранных исполнителей для клиентов"""
    __tablename__ = "favorite_executors"

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True)
    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"), primary_key=True)

    # Added
    client: Mapped["Clients"] = relationship(backref="favorite_executors_associations")
    executor: Mapped["Executors"] = relationship(backref="favorite_clients_associations")


class FavoriteOrders(Base):
    """Many-to-many таблица для хранения избранных заказов для исполнителей"""
    __tablename__ = "favorite_orders"

    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"), primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)

    # Added
    executor: Mapped["Executors"] = relationship(backref="favorite_orders_associations")
    order: Mapped["Orders"] = relationship(backref="favorite_executors_associations")


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
    order: Mapped["Orders"] = relationship(back_populates="files")

    def __str__(self):
        return f"{self.filename}"


class BlockedUsers(Base):
    """Таблица с банами пользователей"""
    __tablename__ = "blocked_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    expire_date: Mapped[datetime.datetime] = mapped_column(nullable=True)
    user_tg_id: Mapped[str] = mapped_column(index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="blocked")

    def __str__(self):
        return f"{self.expire_date}"


class OrdersResponses(Base):
    """Таблица с откликами"""
    __tablename__ = "orders_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    order: Mapped["Orders"] = relationship(back_populates="responses")

    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"))
    executor: Mapped["Executors"] = relationship(back_populates="responses")

    def __str__(self):
        return f"{self.executor_id} -> {self.order_id}"


class ExecutorsViews(Base):
    """Таблица просмотров исполнителей"""
    __tablename__ = "executors_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False)

    executor_id: Mapped[int] = mapped_column(ForeignKey("executors.id", ondelete="CASCADE"))
    executor: Mapped["Executors"] = relationship(back_populates="views")

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    client: Mapped["Clients"] = relationship(back_populates="views")
