from sqlalchemy import select

from database.tables import User, Executors, Availability, Jobs, Professions
from sqladmin.filters import BooleanFilter


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


# class JobsFilter:
#     title = "Направления"
#     parameter_name = "profession"
#
#     def lookups(self, request, model, get_filtered_query) -> list[tuple[str, str]]:
#         """
#         Returns a list of tuples with the filter key and the human-readable label.
#         """
#         with request.state.session as session:
#             rows = (session.execute(select(Professions.id, Professions.title))).all()
#             professions_tuples = [(r.id, r.title) for r in rows]
#         return professions_tuples
#
#     async def get_filtered_query(self, query, value, model):
#         """
#         Returns a filtered query based on the filter value.
#         """
#         return query.filter(Jobs.profession_id == value)


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
