import re

from rest_framework.validators import ValidationError


def validator_username(value):
    """
    Валидатор для поля username.
    Проверяет наличие недопустимых символов
    """
    bad_chars = "".join(re.split(r"^[\w.@+-]+\Z", value))

    if len(bad_chars) != 0:
        raise ValidationError(
            f"Есть недопустимые символы: {bad_chars}"
            f"Для поля `username` не должны приниматься значения $"
        )
