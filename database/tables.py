import datetime

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import text, ForeignKey


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
    role: Mapped[str] = mapped_column(index=True)

    profile: Mapped["Executor"] = relationship(uselist=False, back_populates="user")


class Executor(Base):
    """Таблица профиля исполнителей"""
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[str] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    # TODO может быть сделать отдельной таблицей
    tags: Mapped[str] = mapped_column(nullable=False)

    rate: Mapped[str] = mapped_column(nullable=False)
    experience: Mapped[str] = mapped_column(nullable=False)

    links: Mapped[str] = mapped_column(nullable=False)
    # TODO доступность (в работе/свободен/занят частично)
    availability: Mapped[str] = mapped_column()

    contact: Mapped[str] = mapped_column(nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True)
    is_confirmed: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="profile")
