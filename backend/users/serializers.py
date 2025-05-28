from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Recipe

from .models import Subscription, User


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
        user_id = self.context.get("request").user.id
        return Subscription.objects.filter(
            author=obj.id, user=user_id
        ).exists()


class SubscriptionSerializer(AppUserSerializer):
    """
    Serializer для подписки на автора
    """
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="author.avatar", read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipes.count")

    class Meta:
        model = Subscription
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
        from recipes.serializers import ShortRecipeSerializer

        recipes_limit = self.context.get("request").query_params.get(
            "recipes_limit"
        )

        try:
            recipes_limit = (int(recipes_limit) if recipes_limit is not None
                             else None)
        except ValueError:
            recipes_limit = None

        author_recipes = obj.author.recipes.all()

        if recipes_limit is not None:
            author_recipes = author_recipes[:recipes_limit]

        if author_recipes:
            serializer = ShortRecipeSerializer(
                author_recipes,
                context={"request": self.context.get("request")},
                many=True,
            )
            return serializer.data

        return []

    def get_recipes_count(self, obj):
        """
        Получает количество рецептов у автора
        """
        return Recipe.objects.filter(author=obj.id).count()


class AvatarSerializer(serializers.ModelSerializer):
    """
    Serializer для обновления аватара пользователя
    """
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
