from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from .models import Subscription, User
from .pagination import PageNumberPagination
from recipes.models import Recipe

class CustomUserSerializer(UserSerializer):
    """Проверка подписки."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

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
        )

    def get_is_subscribed(self, obj):
        user_id = self.context.get("request").user.id
        return Subscription.objects.filter(
            author=obj.id, user=user_id
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """При создании пользователя."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        )

class SubscriptionSerializer(CustomUserSerializer, PageNumberPagination):
    """Подписка."""

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipes.count")
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        from backend.recipes.serializers import ShortRecipeSerializer

        author_recipes = obj.author.recipes.all()

        if author_recipes:
            serializer = ShortRecipeSerializer(
                author_recipes,
                context={"request": self.context.get("request")},
                many=True,
            )
            return serializer.data

        return []

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return Recipe.objects.filter(author=obj.id).count()

class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя с полем аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
