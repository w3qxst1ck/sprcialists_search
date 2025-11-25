import datetime
from typing import Any, Callable, List, Tuple

from sqladmin._types import MODEL_ATTR
from sqlalchemy.sql.expression import Select, select
from starlette.requests import Request
from sqlalchemy import Integer


from database.tables import User, Executors, Availability, Jobs, Professions
from sqladmin.filters import BooleanFilter, ForeignKeyFilter, get_column_obj, get_model_from_column, \
    get_foreign_column_name


class RoleFilter:
    title = "Роль"
    parameter_name = "role"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            ("клиент", "клиенты"),
            ("исполнитель", "исполнители"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value == "клиент":
            return query.filter(User.role == "клиент")
        elif value == "исполнитель":
            return query.filter(User.role == "исполнитель")
        else:
            return query


class AdminFilter:
    title = "Администратор"
    parameter_name = "is_admin"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            ("true", "админ-ры"),
            ("false", "не админ-ры"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value == "true":
            return query.filter(User.is_admin == True)
        elif value == "false":
            return query.filter(User.is_admin == False)
        else:
            return query


class BannedFilter:
    title = "Заблокированы"
    parameter_name = "is_banned"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            ("true", "заблокированные"),
            ("false", "не заблокированные"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value == "true":
            return query.filter(User.is_banned == True)
        elif value == "false":
            return query.filter(User.is_banned == False)
        else:
            return query


class VerifiedFilter:
    title = "Верификация"
    parameter_name = "verified"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            ("true", "верифицированные"),
            ("false", "не верифицированные"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value == "true":
            return query.filter(Executors.verified == True)
        elif value == "false":
            return query.filter(Executors.verified == False)
        else:
            return query


class AvailabilityFilter:
    title = "Занятость"
    parameter_name = "availability"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            (Availability.FREE.value, "свободны"),
            (Availability.BUSY.value, "заняты"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value == Availability.FREE.value:
            return query.filter(Executors.availability == Availability.FREE.value)
        elif value == Availability.BUSY.value:
            return query.filter(Executors.availability == Availability.BUSY.value)
        else:
            return query


class JobsForeignKeyFilter(ForeignKeyFilter):
    async def lookups(
        self, request: Request, model: Any, run_query: Callable[[Select], Any]
    ) -> List[Tuple[str, str]]:
        foreign_key_obj = get_column_obj(self.foreign_key, model)
        if self.foreign_model is None and isinstance(self.foreign_display_field, str):
            raise ValueError("foreign_model is required for string foreign key filters")
        if self.foreign_model is None:
            assert not isinstance(self.foreign_display_field, str)
            foreign_display_field_obj = self.foreign_display_field
        else:
            foreign_display_field_obj = get_column_obj(
                self.foreign_display_field, self.foreign_model
            )
        if not self.foreign_model:
            self.foreign_model = get_model_from_column(foreign_display_field_obj)
        foreign_model_key_name = get_foreign_column_name(foreign_key_obj)
        foreign_model_key_obj = getattr(self.foreign_model, foreign_model_key_name)

        return [("", "Все")] + [
            (str(key), str(value))
            for key, value in await run_query(
                select(foreign_model_key_obj, foreign_display_field_obj).distinct()
            )
        ]

    async def get_filtered_query(self, query: Select, value: Any, model: Any) -> Select:
        foreign_key_obj = get_column_obj(self.foreign_key, model)
        column_type = foreign_key_obj.type
        if isinstance(column_type, Integer):
            value = int(value)

        return query.filter(foreign_key_obj == value)


class CreatedDateFilter:
    title = "Дата рег-ии"
    parameter_name = "created_at"

    def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
        """
        Returns a list of tuples with the filter key and the human-readable label.
        """
        return [
            ("all", "все"),
            (3, "3 дня"),
            (7, "неделя"),
            (30, "месяц"),
        ]

    async def get_filtered_query(self, query, value, model):
        """
        Returns a filtered query based on the filter value.
        """
        if value != "all":
            date_from = datetime.datetime.now() - datetime.timedelta(days=int(value))
            return query.filter(model.created_at > date_from)
        else:
            return query
