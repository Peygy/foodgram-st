from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (
    AVATAR_UPLOAD_TO,
    EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    USERNAME_MAX_LENGTH,
)
from .validators import validator_username


class User(AbstractUser):
    """
    Расширенная модель пользователя
    с дополнительными полями и валидацией username
    """
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name="Адрес почты",
        blank=False,
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name="Фамилия"
    )
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        verbose_name="Имя пользователя",
        validators=[
            validator_username,
        ],
    )
    password = models.CharField(
        max_length=PASSWORD_MAX_LENGTH,
        verbose_name="Шифрованный пароль"
    )
    avatar = models.ImageField(
        upload_to=AVATAR_UPLOAD_TO,
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "пользователи"
        ordering = (
            "id",
        )

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель для подписки пользователя
    на другого пользователя (автора)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="author",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "подписку"
        verbose_name_plural = "подписки"

        constraints = [
            models.UniqueConstraint(
                fields=["author", "user"], name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="user_cannot_follow_self",
            ),
        ]

    def __str__(self):
        return f"{self.user} подписан на автора {self.author}"
