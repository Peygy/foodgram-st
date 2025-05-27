from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from rest_framework.decorators import api_view

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAdminAuthorOrReadOnly
from .models import (
    Ingredient,
    Favorite,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
)
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
)

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    """Добавление рецепта."""
    def add(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            return Response(
                {"detail": f"Нельзя повторно добавить рецепт в {name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    """Удаление рецепта из списка пользователя."""
    def delete_from_user(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {"detail": f"Нельзя повторно удалить рецепт из {name}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    """Добавление и удаление рецептов из избранного."""
    @action(
        detail=True,
        methods=("post", "delete"),
        url_path="favorite",
        url_name="favorite",
    )
    def favorite(self, request, pk=None):
        user = request.user
        if request.method == "POST":
            name = "избранное"
            return self.add(Favorite, user, pk, name)
        if request.method == "DELETE":
            name = "избранного"
            return self.delete_from_user(Favorite, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    """Добавление и удаление рецептов из списока покупок."""
    @action(
        detail=True,
        methods=("post", "delete"),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        if request.method == "POST":
            name = "список покупок"
            return self.add(ShoppingCart, user, pk, name)
        if request.method == "DELETE":
            name = "списка покупок"
            return self.delete_from_user(ShoppingCart, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    """Скачивание списока покупок."""
    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        list = (
            RecipeIngredients.objects.filter(recipe__in=recipes)
            .values("ingredient")
            .annotate(amount=Sum("amount"))
        )

        purchased = [
            "Список покупок:",
        ]
        for item in list:
            ingredient = Ingredient.objects.get(pk=item["ingredient"])
            amount = item["amount"]
            purchased.append(
                f"{ingredient.name}: {amount}, "
                f"{ingredient.measurement_unit}"
            )
        purchased_in_file = "\n".join(purchased)

        response = HttpResponse(purchased_in_file, content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=shopping-list.txt"
        return response

    """Получить короткую ссылку на рецепт."""
    @action(
        detail=True,
        methods=("get",),
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f"{request.get_host()}/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)
