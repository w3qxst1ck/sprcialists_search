def is_valid_age(age: str) -> bool:
    """Проверка валидности возраста"""
    try:
        age_int = int(age)
        if 100 < age_int < 18:
            return False
    except ValueError:
        return False
    return True