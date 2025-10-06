import datetime
from enum import Enum

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import text, ForeignKey, String, Enum as SQLEnum


class ClientType(Enum):
    INDIVIDUAL = "индивидуальный предприниматель"
    STUDIO = "студия"
    COMPANY = "компания"


class Availability(Enum):
    FREE = "свободен"
    BUSY = "в работе"
    HALF_BUSY = "занят частично"


class UserRoles(Enum):
    CLIENT = "client"
    EXECUTOR = "executor"


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
    is_banned: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    role: Mapped[str] = mapped_column(SQLEnum(UserRoles), index=True)

    executor_profile: Mapped["Executor"] = relationship(uselist=False, back_populates="user")
    client_profile: Mapped["Client"] = relationship(uselist=False, back_populates="user")


class Client(Base):
    """Таблица с полями профиля клиента"""
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="Имя пользователя должно содержать не более 50 символов")
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(SQLEnum(ClientType), nullable=False)
    links: Mapped[str] = mapped_column(nullable=True, default=None)
    lang: Mapped[str] = mapped_column(nullable=False, default="RUS")
    location: Mapped[str] = mapped_column(nullable=True, default=None)
    verified: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="client_profile")


class Executor(Base):
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
    availability: Mapped[str] = mapped_column(SQLEnum(Availability), default=Availability.FREE, nullable=False)
    contacts: Mapped[str] = mapped_column(nullable=True, default=None)
    location: Mapped[str] = mapped_column(nullable=True, default=None)
    verified: Mapped[bool] = mapped_column(default=False)

    tags: Mapped[list["Tags"]] = relationship(back_populates="executors", secondary="executors_tags")
    user: Mapped["User"] = relationship(back_populates="executor_profile")


class Tags(Base):
    """Таблица с тегами специализации"""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False, index=True, unique=True)

    executors: Mapped[list["Executor"]] = relationship(back_populates="tags", secondary="executors_tags")


class ExecutorsTags(Base):
    """Many-to-many relationship"""
    __tablename__ = "executors_tags"

    executor_id: Mapped[int] = mapped_column(
        ForeignKey("executors.id", ondelete="CASCADE"),
        primary_key=True
    )

    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True
    )

