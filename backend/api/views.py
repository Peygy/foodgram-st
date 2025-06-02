from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from djoser.views import UserViewSet

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
)
from users.models import Subscription, User
from .constants import (
    ACTION_TYPE_ADD,
    ACTION_TYPE_REMOVE,
    ERROR_ALREADY_SUBSCRIBED,
    ERROR_AVATAR_EMPTY,
    ERROR_NOT_SUBSCRIBED,
    ERROR_RECIPE_ALREADY_ADDED,
    ERROR_RECIPE_NOT_FOUND,
    ERROR_SELF_SUBSCRIBE,
)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
    UserAvatarSerializer,
    UserSubscriptionSerializer,
)


class AppUserViewSet(UserViewSet):
    """
    ViewSet для пользователя
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """
        Получить информацию о пользователе
        """
        return super().me(request)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """
        Получить список авторов, на которых подписан пользователь
        """
        subscribed_authors = User.objects.filter(
            author__user=self.request.user,
        )
        pages = self.paginate_queryset(subscribed_authors)
        serializer = UserSubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=("post", "delete"),
    )
    def subscribe(self, request, id=None):
        """
        Подписаться или отписаться от автора
        """
        user = self.request.user
        author = get_object_or_404(User, pk=id)

        if user == author:
            return Response(
                {"detail": ERROR_SELF_SUBSCRIBE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.request.method == "POST":
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": ERROR_ALREADY_SUBSCRIBED},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(author=author, user=user)
            serializer = UserSubscriptionSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            if not Subscription.objects.filter(
                user=user,
                author=author,
            ).exists():
                return Response(
                    {"detail": ERROR_NOT_SUBSCRIBED},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = get_object_or_404(
                Subscription, user=user, author=author
            )
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def update_avatar(self, request):
        """
        Обновить или удалить аватар пользователя
        """
        user = request.user
        if request.method == "PUT":
            avatar_data = request.data.get("avatar")
            if avatar_data is None or avatar_data == "":
                return Response(
                    {"detail": ERROR_AVATAR_EMPTY},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserAvatarSerializer(
                user, data=request.data, partial=True, context={
                    "request": request
                }
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для Ingredient
    """
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для Recipe
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    def get_serializer_class(self):
        """
        Определяет используемый сериализатор
        в зависимости от выполняемого действия
        """
        if self.action in ("create", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        """Сохраняет автора рецепта при создании."""
        serializer.save(author=self.request.user)

    def _handle_recipe_relation(self, model, user, recipe, action_type):
        """
        Обрабатывает добавление/удаление связи между пользователем и рецептом
        """
        relation = model.objects.filter(user=user, recipe=recipe)

        if action_type == ACTION_TYPE_ADD:
            if relation.exists():
                return Response(
                    {"detail": ERROR_RECIPE_ALREADY_ADDED},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not relation.exists():
            return Response(
                {"detail": ERROR_RECIPE_NOT_FOUND},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete"),
        url_path="favorite",
        url_name="favorite",
    )
    def favorite(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из избранного
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        action_type = (ACTION_TYPE_ADD if request.method == "POST"
                       else ACTION_TYPE_REMOVE)
        return self._handle_recipe_relation(
            Favorite, request.user, recipe, action_type
        )

    @action(
        detail=True,
        methods=("post", "delete"),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавляет или удаляет рецепт из списка покупок
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        action_type = (ACTION_TYPE_ADD if request.method == "POST"
                       else ACTION_TYPE_REMOVE)
        return self._handle_recipe_relation(
            ShoppingCart, request.user, recipe, action_type
        )

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        """
        Скачивает список покупок в текстовый файл
        """
        ingredients = (
            RecipeIngredients.objects.filter(
                recipe__shopping_list__user=request.user,
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).annotate(
                total_amount=Sum('amount'),
            ).order_by(
                'ingredient__name',
            )
        )

        purchased = ["Список ваших покупок:"]
        for item in ingredients:
            purchased.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']})"
                f" — {item['total_amount']}"
            )

        response = HttpResponse(
            "\n".join(purchased), content_type="text/plain"
        )
        response["Content-Disposition"] = (
            "attachment; filename=purchased_cart.txt"
        )
        return response

    @action(
        detail=True,
        methods=("get",),
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk=None):
        """
        Получает короткую ссылку на рецепт
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"{request.get_host()}/s/{recipe.id}/"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)
