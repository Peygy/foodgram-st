from django.core.validators import MinValueValidator
from django.db import models

from users.models import User
from .constants import (
    AMOUNT_MIN_VALUE,
    AMOUNT_MIN_VALUE_ERROR_MESSAGE,
    COOKING_TIME_MIN_VALUE,
    COOKING_TIME_MIN_VALUE_ERROR_MESSAGE,
    MAX_FIELD_LENGTH,
    MEASUREMENT_UNIT_DEFAULT,
    RECIPE_IMAGE_UPLOAD_TO,
    RECIPE_NAME_MAX_LENGTH,
)


class Ingredient(models.Model):
    """
    Модель для ингредиента
    """
    name = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name="Название",
        help_text="Название",
    )
    measurement_unit = models.CharField(
        max_length=MAX_FIELD_LENGTH,
        verbose_name="Единица измерения",
        help_text="Единица измерения",
        default=MEASUREMENT_UNIT_DEFAULT,
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"

        constraints = (
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_ingredient",
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Модель для рецепта
    """
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name="Название",
        help_text="Название",
    )
    text = models.TextField(
        verbose_name="Описание",
        help_text="Описание",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredients",
        related_name="recipes",
        verbose_name="Игредиенты",
        help_text="Игредиенты",
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                COOKING_TIME_MIN_VALUE,
                COOKING_TIME_MIN_VALUE_ERROR_MESSAGE
            ),
        ),
        verbose_name="Время приготовления",
        help_text="Время приготовления",
    )
    image = models.ImageField(
        verbose_name="Изображение",
        help_text="Изображение",
        upload_to=RECIPE_IMAGE_UPLOAD_TO,
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикования",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """
    Модель для связи между рецептами и ингредиентами,
    c количеством ингредиента в рецепте
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="ingredient_items"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                AMOUNT_MIN_VALUE,
                AMOUNT_MIN_VALUE_ERROR_MESSAGE
            ),
        ),
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "ингредиенты"
        verbose_name_plural = "ингредиенты"

        constraints = (
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            ),
        )

    def __str__(self):
        return f"В рецепте {self.recipe} есть ингредиент {self.ingredient}"


class Favorite(models.Model):
    """
    Модель для избранных рецептов пользователя
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранные"

        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_favorite_recipe"
            ),
        )

    def __str__(self):
        return f"Рецепт {self.recipe} избранный у {self.user}"


class ShoppingCart(models.Model):
    """
    Модель для списка покупок пользователя
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_list",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "список покупок"
        verbose_name_plural = "списки покупок"

        constraints = (
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_shopping_list_recipe"
            ),
        )

    def __str__(self):
        return (
            f"Рецепт {self.recipe} в списке покупок у {self.user}"
        )
