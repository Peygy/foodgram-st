from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers

from users.serializers import AppUserSerializer

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
)


class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer для Ingredient для представления ингредиентов
    """
    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Serializer для RecipeIngredients
    для представления связей между рецептами и ингредиентами
    """
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredients
        fields = ("id", "name", "measurement_unit", "amount")


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Serializer для создания и обновления связей между рецептами и ингредиентами
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message="Количество ингредиентов не может быть меньше 1"
            ),
        )
    )

    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """
    Основной Serializer для Recipe
    """
    author = AppUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        """
        Метод для получения ингредиентов рецепта
        """
        ingredients = RecipeIngredients.objects.filter(recipe=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        """
        Метод для проверки, добавлен ли рецепт в избранное пользователем
        """
        user_id = self.context.get("request").user.id
        return Favorite.objects.filter(user=user_id, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Метод для проверки, добавлен ли рецепт в список покупок пользователем
        """
        user_id = self.context.get("request").user.id
        return ShoppingCart.objects.filter(
            user=user_id, recipe=obj.id
        ).exists()

    class Meta:
        model = Recipe
        exclude = ("pub_date",)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer для создания и обновления рецептов
    """
    author = AppUserSerializer(read_only=True)
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message="Время приготовления не может быть меньше 1"
            ),
        )
    )

    def validate(self, data):
        """
        Метод валидации данных для создания/обновления рецепта
        """
        if 'image' in data and (data['image'] == '' or data['image'] is None):
            raise serializers.ValidationError(
                {"image": "Изображение рецепта не может быть пустым"}
            )

        if (
            self.context["request"].method == "POST"
            or self.context["request"].method == "PATCH"
        ) and "ingredients" not in data:
            raise serializers.ValidationError(
                {"ingredients": "Добавьте хотя бы один ингредиент!"}
            )

        return data

    def validate_ingredients(self, value):
        """
        Метод валидации списка ингредиентов
        """
        if value is None:
            return None

        if not value:
            raise exceptions.ValidationError(
                "Добавьте хотя бы один ингредиент!"
            )

        ingredients = [item["id"] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    "Рецепт не может включать два одинаковых ингредиента!"
                )

        return value

    def create(self, validated_data):
        """
        Метод для создания нового рецепта
        """
        author = self.context.get("request").user
        ingredients = validated_data.pop("ingredients")

        recipe = Recipe.objects.create(author=author, **validated_data)

        for ingredient in ingredients:
            amount = ingredient.get("amount")
            ingredient = get_object_or_404(
                Ingredient, pk=ingredient.get("id").id
            )

            RecipeIngredients.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        """
        Метод для обновления существующего рецепта
        """
        ingredients = validated_data.pop("ingredients", None)
        if ingredients is not None:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient.get("amount")
                ingredient = get_object_or_404(
                    Ingredient, pk=ingredient.get("id").id
                )

                RecipeIngredients.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient,
                    defaults={"amount": amount},
                )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Метод для представления рецепта после создания/обновления
        """
        serializer = RecipeSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data

    class Meta:
        model = Recipe
        exclude = ("pub_date",)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Краткий Serializer для  Recipe для краткого представления рецептов
    """
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
