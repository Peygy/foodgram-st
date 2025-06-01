from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

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
        from recipes.serializers import ShortRecipeSerializer

        recipes_limit = self.context.get("request").query_params.get(
            "recipes_limit"
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
