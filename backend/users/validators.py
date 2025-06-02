import re

from rest_framework.validators import ValidationError

from .constants import USERNAME_REGEX_PATTERN


def validator_username(value):
    """
    Валидатор для поля username.
    Проверяет наличие недопустимых символов
    """
    # Думаю так будет лучше, проверяем паттерн сразу
    if not re.fullmatch(USERNAME_REGEX_PATTERN, value):
        raise ValidationError(
            "Имя пользователя содержит недопустимые символы."
        )
