from datetime import datetime, timedelta

import pytz
from fastapi import FastAPI
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from starlette.responses import FileResponse

from app.utils import write_csv_file
from database.database import async_session_factory
from database.tables import Executors, Clients, Orders, OrdersResponses, ExecutorsViews
from settings import settings


app = FastAPI()


@app.get("/db")
async def read_root():
    return {"hello": "world"}


# Отправка CSV
@app.get("/export-csv/orders-responses/")
async def export_csv_orders_responses(start_date: str, end_date: str):
    # Переводим время в datetime
    start_date_formatted = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)
    end_date_formatted = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - timedelta(hours=3)

    async with async_session_factory() as session:
        stmt = select(OrdersResponses, Orders, Executors) \
            .join(OrdersResponses.order) \
            .join(OrdersResponses.executor) \
            .where(and_(OrdersResponses.created_at > start_date_formatted, OrdersResponses.created_at < end_date_formatted)) \
            .options(joinedload(OrdersResponses.order)) \
            .options(joinedload(OrdersResponses.executor))
        result = await session.execute(stmt)
        orders_responses = result.scalars().all()

    # Переводим время на МСК
    for item in orders_responses:
        item.created_at = item.created_at.astimezone(tz=pytz.timezone(settings.timezone)).strftime("%d.%m.%Y %H:%M")

    # Записываем файл
    filename = write_csv_file(orders_responses, model="orders_responses", start_date=start_date, end_date=end_date)

    # Отправляем файл
    return FileResponse(path=f"app/files/{filename}", filename=filename, media_type='multipart/form-data')


@app.get("/export-csv/executors-views/")
async def export_csv_executors_views(start_date: str, end_date: str):
    # Переводим время в datetime
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

    # Записываем файл
    filename = write_csv_file(executors_views, model="executors_views", start_date=start_date, end_date=end_date)

    # Отправляем файл
    return FileResponse(path=f"app/files/{filename}", filename=filename, media_type='multipart/form-data')