import validators


def is_valid_age(age: str) -> bool:
    """Проверка валидности возраста"""
    try:
        age_int = int(age)
        if 100 < age_int < 18:
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