from datetime import datetime, timedelta
import pytz
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from database.database import async_session_factory

from sqladmin import BaseView, expose
from database.tables import User, Executors, Clients, Orders, OrdersResponses, ExecutorsViews
from settings import settings


categories = {
    "metrics": ("Метрики", "fa-solid fa-chart-line"),
}


class OrderResponseMetricView(BaseView):
    """Метрики откликов на заказы"""
    name = "Отклики на заказы"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/orders-responses-metric"
    order_details_url = f"{settings.domain}/admin/orders/details/"
    executor_details_url = f"{settings.domain}/admin/executors/details/"

    @expose("/orders-responses-metric", methods=["GET"])
    async def select_metrics_dates(self, request):
        context = {
            "data": None,

            "form_url": self.form_url,
            "order_details_url": self.order_details_url,
            "executor_details_url": self.executor_details_url
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
                .options(joinedload(OrdersResponses.order))\
                .options(joinedload(OrdersResponses.executor))
            result = await session.execute(stmt)
            orders_responses = result.scalars().all()

        # Переводим время на МСК
        for item in orders_responses:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/orders-responses/?start_date={start_date}&end_date={end_date}"

        data = {
            "orders_responses": orders_responses,
            "orders_responses_count": len(orders_responses),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "order_details_url": self.order_details_url,
            "executor_details_url": self.executor_details_url,
            "export_csv_path": export_csv_path
        }
        return await self.templates.TemplateResponse(request, "orders_responses_metric.html", context=context)


class ExecutorsViewsMetricView(BaseView):
    """Метрики просмотров исполнителей"""
    name = "Просмотры исполнителей"
    category = categories["metrics"][0]
    category_icon = categories["metrics"][1]

    # URL для POST запроса формы
    form_url = f"{settings.domain}/admin/executors-views-metric"
    executor_details_url = f"{settings.domain}/admin/executors/details/"
    client_details_url = f"{settings.domain}/admin/clients/details/"

    @expose("/executors-views-metric", methods=["GET"])
    async def select_dates(self, request):
        context = {
            "data": None,

            "form_url": self.form_url,
            "executor_details_url": self.executor_details_url,
            "client_details_url": self.client_details_url
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
                .options(joinedload(ExecutorsViews.executor)) \
                .options(joinedload(ExecutorsViews.client))

            result = await session.execute(stmt)
            executors_views = result.scalars().all()

        # Переводим время на МСК
        for item in executors_views:
            item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

        # Готовим путь для скачивания CSV
        export_csv_path = f"{settings.domain}/export-csv/executors-views/?start_date={start_date}&end_date={end_date}"

        data = {
            "executors_views": executors_views,
            "executors_views_count": len(executors_views),
        }
        context = {
            "data": data,
            "form_url": self.form_url,
            "executor_details_url": self.executor_details_url,
            "client_details_url": self.client_details_url,
            "export_csv_path": export_csv_path
        }
        return await self.templates.TemplateResponse(request, "executors_views_metric.html", context=context)