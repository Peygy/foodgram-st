from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import valid_username


class User(AbstractUser):
    """Модель пользователей."""

    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            valid_username,
        ],
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    password = models.CharField(
        max_length=150,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
    )

    class Meta:
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
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

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
        return f"{self.user} подписан на {self.author}"
