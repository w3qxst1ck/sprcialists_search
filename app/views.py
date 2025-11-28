from datetime import datetime, timedelta

import pytz
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload

from app.filters import AdminFilter, RoleFilter, BannedFilter, VerifiedFilter, AvailabilityFilter, JobsForeignKeyFilter, \
    CreatedDateFilter
from sqladmin import ModelView, BaseView, expose
from database import tables as t
from database.database import async_session_factory
from database.tables import User, Executors, Clients, BlockedUsers, RejectReasons, Orders, Professions, Jobs, \
    OrdersResponses, ExecutorsViews
from settings import settings


categories = {
    "accounts": ("Аккаунты", "fa-solid fa-address-card"),
    "professions": ("Профессии", "fa-solid fa-graduation-cap"),
    "orders": ("Заказы", "fa-solid fa-wallet"),
    "metrics": ("Метрики", "fa-solid fa-chart-line"),
}


class UsersAdmin(ModelView, model=User):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = f"Пользователь"
    name_plural = "Все пользователи"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_list = [User.id, User.tg_id, User.role, User.username,
                   User.created_at, User.updated_at, User.is_banned, User.is_admin]

    column_details_list = [
        User.id, User.tg_id, User.username, User.firstname, User.lastname, User.created_at, User.updated_at,
        User.role, User.executor_profile, User.client_profile, User.is_banned, User.is_admin, User.blocked
    ]

    column_labels = {User.tg_id: "телеграм id", User.role: "роль", User.username: "телеграм username",
                     User.created_at: "дата регистрации", User.updated_at: "дата изменения",
                     User.is_banned: "заблокирован", User.is_admin: "администратор",
                     User.firstname: "имя в телеграм", User.lastname: "фамилия в телеграм",
                     User.executor_profile: "профиль исполнителя", User.client_profile: "профиль заказчика",
                     User.blocked: "блокировка на регистрацию"}

    column_formatters = {
        User.username: lambda u, a: f"@{u.username}",
        User.created_at: lambda u, a: u.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M"),
        User.updated_at: lambda u, a: u.updated_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M") if u.updated_at else '',
    }

    column_formatters_detail = {
        User.username: lambda u, a: f"@{u.username}",
        User.created_at: lambda u, a: u.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M"),
        User.updated_at: lambda u, a: u.updated_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M") if u.updated_at else '',
    }

    column_filters = [
        AdminFilter(),
        BannedFilter(),
        RoleFilter(),
        CreatedDateFilter()
    ]

    column_sortable_list = [User.id, User.role, User.created_at, User.is_banned, User.is_admin]
    column_default_sort = [(User.created_at, True)]

    form_edit_rules = ["is_admin", "is_banned"]

    # icon = "fa-solid fa-user"
    can_create = False
    can_delete = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class BlockedUsersAdmin(ModelView, model=BlockedUsers):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Отмененная анкета"
    name_plural = "Отмененные анкеты"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_exclude_list = [BlockedUsers.user_id, BlockedUsers.id]
    column_details_exclude_list = [BlockedUsers.user_id]

    column_labels = {
        BlockedUsers.expire_date: "срок отказа", BlockedUsers.user_tg_id: "телеграм id",
        BlockedUsers.user: "пользователь",
    }

    column_formatters = {
        BlockedUsers.expire_date: lambda u, a: u.expire_date.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M"),
    }

    column_formatters_detail = {
        BlockedUsers.expire_date: lambda u, a: u.expire_date.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M"),
    }

    # icon = "fa-solid fa-user"
    can_create = False
    can_delete = True
    can_edit = True
    form_edit_rules = ["expire_date"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ExecutorsAdmin(ModelView, model=Executors):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Исполнитель"
    name_plural = "Исполнители"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_list = [
        Executors.id, Executors.tg_id, Executors.name, Executors.age, Executors.description, Executors.rate,
        Executors.experience, Executors.availability, Executors.verified
    ]

    column_details_list = [Executors.id, Executors.tg_id, Executors.user, Executors.name, Executors.age,
                                   Executors.jobs, Executors.description, Executors.rate, Executors.experience,
                                   Executors.links, Executors.contacts, Executors.location, Executors.availability,
                                   Executors.verified]

    column_labels = {Executors.tg_id: "телеграм id", Executors.name: "имя", Executors.age: "возраст",
                     Executors.description: "описание", Executors.rate: "ставка",
                     Executors.experience: "опыт", Executors.links: "ссылки", Executors.availability: "занятость",
                     Executors.contacts: "контакты", Executors.location: "город", Executors.verified: "верифицирован",
                     Executors.photo: "наличие фото", Executors.user: "пользователь", Executors.jobs: "категории",
                     Executors.orders_favorites: "избранные заказы"}

    column_formatters = {
        Executors.description: lambda e, a: e.description[:15] + "..."
    }

    column_formatters_detail = {
        Executors.links: lambda e, a: '    '.join(e.links.split("|"))
    }

    column_filters = [
        VerifiedFilter(),
        AvailabilityFilter()
    ]

    can_create = False
    can_delete = False
    can_edit = True
    form_edit_rules = ["verified", "description"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ClientsAdmin(ModelView, model=Clients):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Заказчик"
    name_plural = "Заказчики"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_list = [
        Clients.id, Clients.tg_id, Clients.name, Clients.orders
    ]

    column_details_list = [Clients.id, Clients.tg_id, Clients.name, Clients.user,
                           Clients.orders, Clients.executors_favorites]

    column_labels = {
        Clients.tg_id: "телеграм id", Clients.name: "имя", Clients.orders: "заказы",
        Clients.executors_favorites: "избранные исполнители"
    }
    # column_filters = [
    #     CreatedDateFilter()
    # ]

    can_create = False
    can_delete = False
    can_edit = True
    form_edit_rules = ["name"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ProfessionsAdmin(ModelView, model=t.Professions):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Направление"
    name_plural = "Направления"
    category = categories["professions"][0]
    category_icon = categories["professions"][1]

    column_list = [Professions.id, Professions.title, Professions.emoji]
    column_details_list = [Professions.id, Professions.title, Professions.emoji, Professions.jobs]
    column_labels = {
        Professions.id: "id",
        Professions.title: "название",
        Professions.emoji: "emoji",
        Professions.jobs: "категории"
    }

    form_edit_rules = ["title", "emoji"]
    form_create_rules = ["title", "emoji"]

    can_create = True
    can_delete = True
    can_edit = True

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class JobsAdmin(ModelView, model=t.Jobs):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Категория"
    name_plural = "Категории"
    category = categories["professions"][0]
    category_icon = categories["professions"][1]

    column_list = [Jobs.id, Jobs.title, Jobs.profession]
    column_details_list = [Jobs.id, Jobs.title, Jobs.profession]
    column_labels = {Jobs.id: "id", Jobs.title: "название", Jobs.profession: "направление"}

    form_edit_rules = ["title"]
    form_create_rules = ["title", "profession"]

    can_create = True
    can_delete = True
    can_edit = True

    page_size = 25
    page_size_options = [10, 25, 50, 100]

    column_filters = [JobsForeignKeyFilter(Jobs.profession_id, Professions.title, title="Направления")]


class RejectReasonsAdmin(ModelView, model=RejectReasons):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Причина отказа"
    name_plural = "Причины отказа"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_exclude_list = [RejectReasons.id]

    column_labels = {
        RejectReasons.reason: "причина",
        RejectReasons.text: "описание",
        RejectReasons.period: "дней блокировки",
    }

    column_formatters = {
        RejectReasons.text: lambda r, a: r.text[:15] + "..."
    }

    can_edit = True
    can_create = True
    can_delete = True
    can_export = False


class OrdersAdmin(ModelView, model=Orders):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Заказ"
    name_plural = "Заказы"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]

    column_list = [
        Orders.client, Orders.title, Orders.created_at, Orders.is_active, Orders.price, Orders.period, Orders.jobs
    ]
    column_details_list = [
        Orders.id, Orders.client, Orders.jobs, Orders.title, Orders.task, Orders.price, Orders.period,
        Orders.requirements, Orders.files, Orders.created_at, Orders.is_active, Orders.executors_favorites
    ]

    column_labels = {
        Orders.client: "заказчик", Orders.jobs: "категории", Orders.files: "файлы",
        Orders.executors_favorites: "в избранном", Orders.tg_id: "телеграм id", Orders.title: "название",
        Orders.task: "описание задачи", Orders.price: "цена", Orders.requirements: "требования",
        Orders.period: "срок выполнения", Orders.created_at: "дата размещения", Orders.is_active: "активен",
    }

    column_formatters = {
        Orders.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
    }

    column_formatters_detail = {
        Orders.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
    }
    # column_filters = [
    #     ForeignKeyFilter(Orders.client_id, Clients.name, title="Заказчик")
    # ]

    column_sortable_list = [Orders.created_at]
    column_default_sort = [(Orders.created_at, True)]

    can_delete = True
    can_edit = True
    form_edit_rules = ["is_active"]
    can_create = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class OrdersResponsesAdmin(ModelView, model=OrdersResponses):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Отклик на заказ"
    name_plural = "Отклики на заказы"
    category = categories["orders"][0]
    category_icon = categories["orders"][1]

    column_list = [OrdersResponses.order, OrdersResponses.executor, OrdersResponses.text, OrdersResponses.created_at]
    column_details_list = [
        OrdersResponses.id, OrdersResponses.order, OrdersResponses.executor, OrdersResponses.text,
        OrdersResponses.created_at,
    ]

    column_labels = {
        OrdersResponses.order: "заказ",
        OrdersResponses.executor: "исполнитель",
        OrdersResponses.created_at: "дата",
        OrdersResponses.text: "текст"
    }

    column_formatters = {
        OrdersResponses.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
        OrdersResponses.text: lambda o, a: o.text[:15] + "..."
    }

    column_formatters_detail = {
        OrdersResponses.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
        OrdersResponses.text: lambda o, a: f"\"{o.text}\""
    }

    # column_filters = [
    #     ForeignKeyFilter(OrdersResponses.executor_id, Executors.name, title="Исполнители"),
    #     ForeignKeyFilter(OrdersResponses.order_id, Orders.title, title="Заказы"),
    # ]

    can_delete = False
    can_edit = False
    can_create = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ExecutorsViewsAdmin(ModelView, model=ExecutorsViews):
    # Templates
    edit_template = "custom_edit.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    create_template = "custom_create.html"

    name = "Просмотр исполнителя"
    name_plural = "Просмотры исполнителей"
    category = categories["orders"][0]
    category_icon = categories["orders"][1]

    column_list = [ExecutorsViews.executor, ExecutorsViews.client, ExecutorsViews.created_at]

    column_details_list = [
        ExecutorsViews.id, ExecutorsViews.executor, ExecutorsViews.client, ExecutorsViews.created_at
    ]

    column_labels = {
        ExecutorsViews.executor: "исполнитель", ExecutorsViews.client: "заказчик", ExecutorsViews.created_at: "дата",
    }

    column_formatters = {
        ExecutorsViews.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
    }
    column_formatters_detail = {
        ExecutorsViews.created_at: lambda o, a: o.created_at.astimezone(
            tz=pytz.timezone(settings.timezone)
        ).strftime("%d.%m.%Y %H:%M"),
    }

    # column_filters = [
    #     ForeignKeyFilter(ExecutorsViews.executor_id, Executors.name, title="Исполнители"),
    #     ForeignKeyFilter(ExecutorsViews.client_id, Clients.name, title="Заказчики"),
    # ]

    can_delete = False
    can_edit = False
    can_create = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


# CUSTOM VIEWS
class OrderResponseMetricView(BaseView):
    """Метрики откликов на заказы"""
    name = "Отклики на заказы"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]
    title = "Отклики на заказы"

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/orders-responses-metric"
    order_details_url = f"{settings.domain}/admin/orders/details/"
    executor_details_url = f"{settings.domain}/admin/executors/details/"

    @expose("/orders-responses-metric", methods=["GET"])
    async def select_metrics_dates(self, request):
        context = {
            "data": None,
            "form_url": self.form_url,
            "title": self.title,
        }
        return await self.templates.TemplateResponse(request, "orders_responses_metric.html", context=context)

    @expose("/orders-responses-metric", methods=["POST"])
    async def metrics_period_page(self, request):
        # Получаем данные из request
        form_data = await request.form()
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")

        # Переводим даты из строк в datetime и вычитаем три часа для нормального сравнения в БД
        start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
        end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)

        async with async_session_factory() as session:
            stmt = select(OrdersResponses, Orders, Executors)\
                .join(OrdersResponses.order)\
                .join(OrdersResponses.executor)\
                .where(and_(OrdersResponses.created_at > start_date_formatted, OrdersResponses.created_at < end_date_formatted))\
                .order_by(desc(OrdersResponses.created_at))\
                .options(joinedload(OrdersResponses.order))\
                .options(joinedload(OrdersResponses.executor))
            result = await session.execute(stmt)
            orders_responses = result.scalars().all()

        # Переводим время на МСК
        for item in orders_responses:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/orders-responses/?start_date={start_date}&end_date={end_date}"

        # Даты для вывода в subtitle
        start_date_str = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        end_date_str = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")

        data = {
            "orders_responses": orders_responses,
            "orders_responses_count": len(orders_responses),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "order_details_url": self.order_details_url,
            "executor_details_url": self.executor_details_url,
            "export_csv_path": export_csv_path,
            "title": self.title,
            "subtitle": f"{start_date_str} - {end_date_str}"
        }
        return await self.templates.TemplateResponse(request, "orders_responses_metric.html", context=context)


class ExecutorsViewsMetricView(BaseView):
    """Метрики просмотров исполнителей"""
    name = "Просмотры исполнителей"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]
    title = "Просмотры исполнителей"

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/executors-views-metric"
    executor_details_url = f"{settings.domain}/admin/executors/details/"
    client_details_url = f"{settings.domain}/admin/clients/details/"

    @expose("/executors-views-metric", methods=["GET"])
    async def select_dates(self, request):
        context = {
            "data": None,
            "form_url": self.form_url,
            "title": self.title,
        }
        return await self.templates.TemplateResponse(request, "executors_views_metric.html", context=context)

    @expose("/executors-views-metric", methods=["POST"])
    async def metrics(self, request):
        form_data = await request.form()
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")

        # Переводим даты из строк в datetime и вычитаем три часа для нормального сравнения в БД
        start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
        end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)

        async with async_session_factory() as session:
            stmt = select(ExecutorsViews, Executors, Clients) \
                .join(ExecutorsViews.executor) \
                .join(ExecutorsViews.client) \
                .where(and_(ExecutorsViews.created_at > start_date_formatted, ExecutorsViews.created_at < end_date_formatted)) \
                .order_by(desc(ExecutorsViews.created_at))\
                .options(joinedload(ExecutorsViews.executor)) \
                .options(joinedload(ExecutorsViews.client))

            result = await session.execute(stmt)
            executors_views = result.scalars().all()

        # Переводим время на МСК
        for item in executors_views:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/executors-views/?start_date={start_date}&end_date={end_date}"

        # Даты для вывода в subtitle
        start_date_str = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        end_date_str = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")

        data = {
            "executors_views": executors_views,
            "executors_views_count": len(executors_views),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "executor_details_url": self.executor_details_url,
            "client_details_url": self.client_details_url,
            "export_csv_path": export_csv_path,
            "title": self.title,
            "subtitle": f"{start_date_str} - {end_date_str}"
        }
        return await self.templates.TemplateResponse(request, "executors_views_metric.html", context=context)


class ExecutorsRegistrationMetricView(BaseView):
    """Метрики регистрации исполнителей"""
    name = "Регистрация исполнителей"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]
    title = "Регистрация исполнителей"

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/executors-registration-metric"
    executor_details_url = f"{settings.domain}/admin/executors/details/"

    @expose("/executors-registration-metric", methods=["GET"])
    async def select_dates_ex_registration(self, request):
        context = {
            "data": None,
            "form_url": self.form_url,
            "title": self.title
        }
        return await self.templates.TemplateResponse(request, "executors_registration_metric.html", context=context)

    @expose("/executors-registration-metric", methods=["POST"])
    async def metrics_ex_registration(self, request):
        form_data = await request.form()
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")

        # Переводим даты из строк в datetime и вычитаем три часа для нормального сравнения в БД
        start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
        end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)

        async with async_session_factory() as session:
            stmt = select(Executors, User) \
                .join(Executors.user) \
                .where(and_(Executors.created_at > start_date_formatted, Executors.created_at < end_date_formatted)) \
                .order_by(desc(Executors.created_at))\
                .options(joinedload(Executors.user))

            result = await session.execute(stmt)
            executors = result.scalars().all()

        # Переводим время на МСК
        for item in executors:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/executors-registration/?start_date={start_date}&end_date={end_date}"

        # Даты для вывода в subtitle
        start_date_str = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        end_date_str = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")

        data = {
            "executors": executors,
            "executors_count": len(executors),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "executor_details_url": self.executor_details_url,
            "export_csv_path": export_csv_path,
            "title": self.title,
            "subtitle": f"{start_date_str} - {end_date_str}"
        }
        return await self.templates.TemplateResponse(request, "executors_registration_metric.html", context=context)


class ClientsRegistrationMetricView(BaseView):
    """Метрики регистрации клиентов"""
    name = "Регистрация клиентов"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]
    title = "Регистрация клиентов"

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/clients-registration-metric"
    clients_details_url = f"{settings.domain}/admin/clients/details/"

    @expose("/clients-registration-metric", methods=["GET"])
    async def select_dates_cli_registration(self, request):
        context = {
            "data": None,
            "form_url": self.form_url,
            "title": self.title
        }
        return await self.templates.TemplateResponse(request, "clients_registration_metric.html", context=context)

    @expose("/clients-registration-metric", methods=["POST"])
    async def metrics_cli_registration(self, request):
        form_data = await request.form()
        start_date = form_data.get("start_date")
        end_date = form_data.get("end_date")

        # Переводим даты из строк в datetime и вычитаем три часа для нормального сравнения в БД
        start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
        end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)

        async with async_session_factory() as session:
            stmt = select(Clients, User) \
                .join(Clients.user) \
                .where(and_(Clients.created_at > start_date_formatted, Clients.created_at < end_date_formatted)) \
                .order_by(desc(Clients.created_at))\
                .options(joinedload(Clients.user))

            result = await session.execute(stmt)
            clients = result.scalars().all()

        # Переводим время на МСК
        for item in clients:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/clients-registration/?start_date={start_date}&end_date={end_date}"

        # Даты для вывода в subtitle
        start_date_str = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        end_date_str = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")

        data = {
            "clients": clients,
            "clients_count": len(clients),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "client_details_url": self.clients_details_url,
            "export_csv_path": export_csv_path,
            "title": self.title,
            "subtitle": f"{start_date_str} - {end_date_str}"
        }
        return await self.templates.TemplateResponse(request, "clients_registration_metric.html", context=context)


# class TaskFilesAdmin(ModelView, model=t.TaskFiles):
#     column_list = "__all__"
#
#     name = "Файл заказа"
#     name_plural = "Файлы заказов"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]

# class FavoriteExecutorsAdmin(ModelView, model=t.FavoriteExecutors):
#     column_list = "__all__"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]
#
#
# class FavoriteOrdersAdmin(ModelView, model=t.FavoriteOrders):
#     column_list = "__all__"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]
#
#
# class OrdersJobsAdmin(ModelView, model=t.OrdersJobs):
#     column_list = "__all__"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]
#
#
# class ExecutorsJobsAdmin(ModelView, model=t.ExecutorsJobs):
#     column_list = "__all__"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]