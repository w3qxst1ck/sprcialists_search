import validators


def is_valid_age(age: str) -> bool:
    """Проверка валидности возраста"""
    try:
        age_int = int(age)
        if 100 < age_int or age_int < 18:
            return False
    except ValueError:
        return False
    return True


def is_valid_url(url: str) -> bool:
    """Проверка валидности ссылок"""
    return validators.url(url)


def is_valid_price(price: str) -> bool:
    """Проверка валидности цены заказа"""
    try:
        int(price)
    except ValueError:
        return False
    return True


def is_valid_deadline(days: str) -> bool:
    """Проверка валидности дедлайна"""
    try:
        days_int = int(days)
        if days_int < 1:
            return False
    except ValueError:
        return False
    return True