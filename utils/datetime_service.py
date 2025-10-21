import datetime
import calendar


def get_days_in_month(year: int, month: int) -> list[datetime.date]:
    """Возвращает список всех дней в заданном месяце датами"""
    # количество дней в месяце
    _, num_days = calendar.monthrange(year, month)

    start_date = datetime.date(year, month, 1)
    all_days = []
    for i in range(num_days):
        all_days.append(start_date + datetime.timedelta(days=i))

    return all_days


def get_next_and_prev_month_and_year(month: int, year: int) -> dict:
    """Расчет следующего и предыдущего месяцев и года"""
    result = {}
    if month == 1:
        result["prev_month"] = 12
        result["next_month"] = 2
        result["prev_year"] = year - 1
        result["next_year"] = year
    elif month == 12:
        result["prev_month"] = 11
        result["next_month"] = 1
        result["prev_year"] = year
        result["next_year"] = year + 1
    else:
        result["prev_month"] = month - 1
        result["next_month"] = month + 1
        result["prev_year"] = year
        result["next_year"] = year

    return result


def convert_str_to_datetime(date_str: str) -> datetime.datetime:
    """Перевод из строки в datetime. Необходима строка формата d.m.y"""
    return datetime.datetime.strptime(date_str, "%d.%m.%Y")


def convert_date_time_to_str(date: datetime.datetime, with_tz: bool = None) -> (str, str):
    """Перевод даты в формат для вывода (date, time)"""
    return date.date().strftime("%d.%m.%Y")


def get_days_left_text(days: int) -> str:
    """Формулировка дней в зависимости от числа"""
    days_str = str(days)

    if days_str[-1] in ("5", "6", "7", "8", "9", "0") or 10 < days < 20:
        return "дней"

    if days_str[-1] in ("2", "3", "4"):
        return "дня"

    if days_str[-1] == "1":
        return "день"
