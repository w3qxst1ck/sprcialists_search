def get_age_text(age: int) -> str:
    """Правильная формулировка возраста"""
    age_str = str(age)

    if age_str[-1] in ["0", "5", "6", "7", "8", "9"]:
        return f"{age} лет"
    elif age_str[-1] in ["2", "3", "4"]:
        return f"{age} года"
    else:
        return f"{age} год"