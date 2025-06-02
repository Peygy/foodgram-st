from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField

from recipes.constants import AMOUNT_MIN_VALUE, AMOUNT_MIN_VALUE_ERROR_MESSAGE
from recipes.models import Ingredient, Recipe, RecipeIngredients
from users.models import User
from .constants import RECIPES_LIMIT_QUERY_PARAM


class AppUserCreateSerializer(UserCreateSerializer):
    """
    Serializer для создания нового пользователя
    """
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        )


class AppUserSerializer(UserSerializer):
    """
    Serializer для информации о пользователе
    """
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного пользователя
        """
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.author.filter(user=user).exists()
        return False


class UserSubscriptionSerializer(AppUserSerializer):
    """
    Serializer для подписки на автора
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "avatar",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """
        Получает список рецептов автора с учетом лимита
        """
        recipes_limit = self.context.get("request").query_params.get(
            RECIPES_LIMIT_QUERY_PARAM
        )
        try:
            recipes_limit = (int(recipes_limit) if recipes_limit is not None
                             else None)
        except ValueError:
            recipes_limit = None

        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]

        return ShortRecipeSerializer(
            recipes,
            context={"request": self.context.get("request")},
            many=True
        ).data


class UserAvatarSerializer(serializers.ModelSerializer):
    """
    Serializer для обновления аватара пользователя
    """
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


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
        # Не дублируем написание валидатора из модели
        extra_kwargs = {
            'amount': {
                'min_value': AMOUNT_MIN_VALUE,
                'error_messages': {
                    'min_value': AMOUNT_MIN_VALUE_ERROR_MESSAGE
                }
            }
        }


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """
    Serializer для создания и обновления связей между рецептами и ингредиентами
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredients
        fields = ("id", "amount")
        # Не дублируем написание валидатора из модели
        extra_kwargs = {
            'amount': {
                'min_value': AMOUNT_MIN_VALUE,
                'error_messages': {
                    'min_value': AMOUNT_MIN_VALUE_ERROR_MESSAGE
                }
            }
        }


class RecipeSerializer(serializers.ModelSerializer):
    """
    Основной Serializer для Recipe
    """
    author = AppUserSerializer(read_only=True)
    ingredients = RecipeIngredientsSerializer(
        source='ingredient_items',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ("pub_date",)

    def get_is_favorited(self, obj):
        """
        Метод для проверки, добавлен ли рецепт в избранное пользователем
        """
        user = self.context.get("request").user
        if user.is_authenticated:
            return user.favorite.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """
        Метод для проверки, добавлен ли рецепт в список покупок пользователем
        """
        user = self.context.get("request").user
        if user.is_authenticated:
            return user.shopping_list.filter(
                recipe=obj,
            ).exists()
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer для создания и обновления рецептов
    """
    author = AppUserSerializer(read_only=True)
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        exclude = ("pub_date",)

    def validate(self, data):
        """
        Метод валидации данных для создания/обновления рецепта
        """
        if 'image' in data and (data['image'] == '' or data['image'] is None):
            raise serializers.ValidationError(
                {"image": "Изображение рецепта не может быть пустым"}
            )

        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {"ingredients": "Добавьте хотя бы один ингредиент!"}
            )

        ingredient_ids = [item["id"] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {
                    "ingredients":
                    "Рецепт не может включать два одинаковых ингредиента!"
                }
            )

        return data

    def _create_ingredients(self, recipe, ingredients_data):
        """Создает связи между рецептом и ингредиентами."""
        RecipeIngredients.objects.bulk_create([
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient_data["id"],
                amount=ingredient_data["amount"]
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        """
        Метод для создания нового рецепта
        """
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """
        Метод для обновления существующего рецепта
        """
        ingredients_data = validated_data.pop("ingredients")
        instance.ingredients.clear()
        self._create_ingredients(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Метод для представления рецепта после создания/обновления
        """
        return RecipeSerializer(
            instance,
            context={"request": self.context.get("request")}
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Краткий Serializer для  Recipe для краткого представления рецептов
    """
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
