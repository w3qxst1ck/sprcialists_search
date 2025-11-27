from typing import List, Any
import csv


def write_csv_file(data: List[Any], model: str, start_date: str, end_date: str) -> str:
    """Создает csv файл, возвращает путь до файла"""
    filename = f"{start_date}-{end_date}.csv"
    values = []
    headers = []

    # Запись метрик откликов на заказы
    if model == "orders_responses":
        headers = ["№ п/п", "Заказ", "Исполнитель", "Текст", "Дата"]

        for idx, item in enumerate(data, start=1):
            row = [idx, item.order.title, item.executor.name, item.text, item.created_at]
            values.append(row)

    # Запись метрик просмотра исполнителей
    elif model == "executors_views":
        headers = ["№ п/п", "Исполнитель", "Заказчик", "Дата"]

        for idx, item in enumerate(data, start=1):
            row = [idx, item.executor.name, item.client.name, item.created_at]
            values.append(row)

    # Запись метрик регистрации исполнителей
    elif model == "executors_registration":
        headers = ["№ п/п", "Id", "Телеграмм id", "Имя", "Возраст", "Описание", "Верифицирован", "Дата регистрации"]

        for idx, item in enumerate(data, start=1):
            if item.verified:
                verified_formatted = "Да"
            else:
                verified_formatted = "Нет"

            row = [idx, item.id, item.tg_id, item.name, item.age, item.description, verified_formatted, item.created_at]
            values.append(row)

    # Запись метрик регистрации клиентов
    elif model == "clients_registration":
        headers = ["№ п/п", "Id", "Телеграмм id", "Имя", "Дата регистрации"]

        for idx, item in enumerate(data, start=1):
            row = [idx, item.id, item.tg_id, item.name, item.created_at]
            values.append(row)

    with open(f"app/files/{filename}", 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Записываем заголовки
        writer.writerow(headers)

        # Записываем данные
        for value in values:
            writer.writerow(value)

    return filename