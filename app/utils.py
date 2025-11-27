import datetime
from typing import List, Any
import uuid
import csv

from sqlalchemy import inspect


def write_csv_file(data: List[Any], model: str, start_date: str, end_date: str) -> str:
    """Создает csv файл, возвращает путь до файла"""
    # Случайное имя
    filename = f"{start_date}-{end_date}.csv"
    values = []
    headers = []

    # with open(f"app/files/{filename}", 'w', newline='', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    #
    #     # Записываем заголовки
    #     headers = [c.key for c in inspect(data[0]).mapper.column_attrs]
    #     writer.writerow(headers)
    #
    #     for item in data:
    #         # Получаем значения полей из модели
    #         values = [getattr(item, c.key) for c in inspect(item).mapper.column_attrs]
    #         writer.writerow(values)

    if model == "orders_responses":
        headers = ["№ п/п", "Заказ", "Исполнитель", "Текст", "Дата"]

        for idx, item in enumerate(data, start=1):
            row = [idx, item.order.title, item.executor.name, item.text, item.created_at]
            values.append(row)

    elif model == "executors_views":
        headers = ["№ п/п", "Исполнитель", "Заказчик", "Дата"]

        for idx, item in enumerate(data, start=1):
            row = [idx, item.executor.name, item.client.name, item.created_at]
            values.append(row)

    with open(f"app/files/{filename}", 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Записываем заголовки
        writer.writerow(headers)

        # Записываем данные
        for value in values:
            writer.writerow(value)

    return filename