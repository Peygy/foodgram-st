import re
from rest_framework.validators import ValidationError

def valid_username(value):
    """Проверка имени и возврат не корректных символов."""
    bad_chars = "".join(re.split(r"[\w]|[.]|[@]|[+]|[-]+$", value))

    if len(bad_chars) != 0:
        raise ValidationError(
            f"Есть недопустимые символы: {bad_chars}"
            f"Не допускаются: пробел(перенос строки и т.п) и символы, кроме . @ + - _"
        )
