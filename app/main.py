from sqladmin.authentication import login_required
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

from app.auth import authentication_backend
from database.database import async_engine
from sqladmin import Admin

from app.views import UsersAdmin, ExecutorsAdmin, ClientsAdmin, BlockedUsersAdmin, RejectReasonsAdmin, \
    ProfessionsAdmin, JobsAdmin, OrdersAdmin, OrdersResponsesAdmin, ExecutorsViewsAdmin
from app.custom_views import OrderResponseMetricView, ExecutorsViewsMetricView
from app.fastapi_app import app as fastapi_app


class CustomAdmin(Admin):
    @login_required
    async def index(self, request: Request) -> Response:
        """Index route which can be overridden to create dashboards."""

        return await self.templates.TemplateResponse(request, "custom_index.html")

    async def login(self, request: Request) -> Response:
        assert self.authentication_backend is not None

        context = {}
        if request.method == "GET":
            return await self.templates.TemplateResponse(request, "custom_login.html")

        ok = await self.authentication_backend.login(request)
        if not ok:
            context["error"] = "Invalid credentials."
            return await self.templates.TemplateResponse(
                request, "custom_login.html", context, status_code=400
            )

        return RedirectResponse(request.url_for("admin:index"), status_code=302)


admin = CustomAdmin(fastapi_app, async_engine, authentication_backend=authentication_backend,
                    templates_dir="app/templates/sqladmin/", title="PRUV ADMIN")

admin.add_view(UsersAdmin)
admin.add_view(ExecutorsAdmin)
admin.add_view(ClientsAdmin)
admin.add_view(BlockedUsersAdmin)
admin.add_view(RejectReasonsAdmin)

admin.add_view(ProfessionsAdmin)
admin.add_view(JobsAdmin)

admin.add_view(OrdersAdmin)
admin.add_view(OrdersResponsesAdmin)
admin.add_view(ExecutorsViewsAdmin)

admin.add_view(OrderResponseMetricView)
admin.add_view(ExecutorsViewsMetricView)

# admin.add_view(TaskFilesAdmin)
# admin.add_view(FavoriteExecutorsAdmin)
# admin.add_view(FavoriteOrdersAdmin)
# admin.add_view(OrdersJobsAdmin)
# admin.add_view(ExecutorsJobsAdmin)

