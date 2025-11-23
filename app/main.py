import pytz
from fastapi import FastAPI
from sqladmin.filters import BooleanFilter, ForeignKeyFilter

from app.filters import AdminFilter, RoleFilter, BannedFilter, VerifiedFilter, AvailabilityFilter
from database.database import async_engine
from sqladmin import Admin, ModelView
from database import tables as t
from database.tables import User, Executors, Clients, BlockedUsers, RejectReasons, Orders
from settings import settings

app = FastAPI()


categories = {
    "accounts": ("Аккаунты", "fa-solid fa-address-card"),
    "professions": ("Профессии", "fa-solid fa-graduation-cap"),
    "orders": ("Заказы", "fa-solid fa-wallet"),
}


@app.get("/db")
async def read_root():
    return {"hello": "world"}


app = FastAPI()
admin = Admin(app, async_engine)


class UsersAdmin(ModelView, model=User):
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
        User.updated_at: lambda u, a: u.updated_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M") if u.updated_at else None,
    }

    column_formatters_detail = {
        User.username: lambda u, a: f"@{u.username}",
        User.created_at: lambda u, a: u.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M"),
        User.updated_at: lambda u, a: u.updated_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M") if u.updated_at else None,
    }

    column_filters = [
        AdminFilter(),
        BannedFilter(),
        RoleFilter()
    ]

    form_edit_rules = ["is_admin", "is_banned"]

    # icon = "fa-solid fa-user"
    can_create = False
    can_delete = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class BlockedUsersAdmin(ModelView, model=BlockedUsers):
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
    can_create = True
    can_delete = True
    can_edit = True
    form_edit_rules = ["expire_date"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ExecutorsAdmin(ModelView, model=Executors):
    name = "Исполнитель"
    name_plural = "Исполнители"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_list = [
        Executors.id, Executors.tg_id, Executors.name, Executors.age, Executors.description, Executors.rate,
        Executors.experience, Executors.availability, Executors.verified
    ]

    column_details_exclude_list = [Executors.clients_favorites]

    column_labels = {Executors.tg_id: "телеграм id", Executors.name: "имя", Executors.age: "возраст",
                     Executors.description: "описание", Executors.rate: "ставка",
                     Executors.experience: "опыт", Executors.links: "ссылки", Executors.availability: "занятость",
                     Executors.contacts: "контакты", Executors.location: "город", Executors.verified: "верифицирован",
                     Executors.photo: "наличие фото", Executors.user: "пользователь", Executors.jobs: "категории",
                     Executors.orders_favorites: "избранные заказы"}

    column_formatters = {
        Executors.description: lambda e, a: e.description[:15] + "...",
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

    can_create = False
    can_delete = False
    can_edit = True
    form_edit_rules = ["name"]

    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ProfessionsAdmin(ModelView, model=t.Professions):
    column_list = "__all__"

    name = "Направление"
    name_plural = "Направления"

    category = categories["professions"][0]
    category_icon = categories["professions"][1]


class JobsAdmin(ModelView, model=t.Jobs):
    column_list = "__all__"

    name = "Категория"
    name_plural = "Категории"

    category = categories["professions"][0]
    category_icon = categories["professions"][1]


class RejectReasonsAdmin(ModelView, model=RejectReasons):
    name = "Причина отказа"
    name_plural = "Причины отказа"
    category = categories["accounts"][0]
    category_icon = categories["accounts"][1]

    column_exclude_list = [RejectReasons.id]

    column_labels = {
        RejectReasons.reason: "причина", RejectReasons.text: "описание", RejectReasons.period: "период блокировки",
    }

    column_formatters = {
        RejectReasons.text: lambda r, a: r.text[:15] + "..."
    }

    can_edit = True
    can_create = True
    can_delete = True


class OrdersAdmin(ModelView, model=Orders):
    name = "Заказ"
    name_plural = "Заказы"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]

    column_list = [Orders.client, Orders.title, Orders.jobs, Orders.price, Orders.period, Orders.created_at]
    column_details_list = [
        Orders.id, Orders.client, Orders.jobs, Orders.title, Orders.task, Orders.price, Orders.period,
        Orders.requirements, Orders.files, Orders.created_at, Orders.is_active, Orders.executors_favorites
    ]

    column_default_sort = [(Orders.created_at, True)]

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
    column_filters = [
        ForeignKeyFilter(Orders.client_id, Clients.name, title="Заказчик")
    ]

    can_delete = True
    can_edit = True
    form_edit_rules = ["is_active"]
    can_create = False

    page_size = 25
    page_size_options = [10, 25, 50, 100]


# class TaskFilesAdmin(ModelView, model=t.TaskFiles):
#     column_list = "__all__"
#
#     name = "Файл заказа"
#     name_plural = "Файлы заказов"
#
#     category = categories["orders"][0]
#     category_icon = categories["orders"][1]


class FavoriteExecutorsAdmin(ModelView, model=t.FavoriteExecutors):
    column_list = "__all__"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]


class FavoriteOrdersAdmin(ModelView, model=t.FavoriteOrders):
    column_list = "__all__"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]


class OrdersJobsAdmin(ModelView, model=t.OrdersJobs):
    column_list = "__all__"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]


class ExecutorsJobsAdmin(ModelView, model=t.ExecutorsJobs):
    column_list = "__all__"

    category = categories["orders"][0]
    category_icon = categories["orders"][1]


admin.add_view(UsersAdmin)
admin.add_view(ExecutorsAdmin)
admin.add_view(ClientsAdmin)
admin.add_view(BlockedUsersAdmin)
admin.add_view(RejectReasonsAdmin)

admin.add_view(ProfessionsAdmin)
admin.add_view(JobsAdmin)

admin.add_view(OrdersAdmin)

# admin.add_view(TaskFilesAdmin)
# admin.add_view(FavoriteExecutorsAdmin)
# admin.add_view(FavoriteOrdersAdmin)
# admin.add_view(OrdersJobsAdmin)
# admin.add_view(ExecutorsJobsAdmin)

