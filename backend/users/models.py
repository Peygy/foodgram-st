from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Адрес почты",
        blank=False,
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name="Фамилия"
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Имя пользователя"
    )
    password = models.CharField(
        max_length=150,
        verbose_name="Шифрованный пароль"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "пользователи"
        ordering = ("id",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки."""

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
