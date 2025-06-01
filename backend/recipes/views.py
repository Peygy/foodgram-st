from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
)
from .pagination import CustomPageNumberPagination
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShortRecipeSerializer,
)


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
    pagination_class = CustomPageNumberPagination

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
        
        if action_type == 'add':
            if relation.exists():
                return Response(
                    {"detail": "Рецепт уже добавлен"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if not relation.exists():
            return Response(
                {"detail": "Рецепт не найден"},
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
        action_type = 'add' if request.method == "POST" else 'remove'
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
        action_type = 'add' if request.method == "POST" else 'remove'
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
            RecipeIngredients.objects
            .filter(recipe__shopping_list__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        purchased = ["Список ваших покупок:"]
        for item in ingredients:
            purchased.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )

        response = HttpResponse("\n".join(purchased), content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=purchased_cart.txt"
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
        short_link = f"{request.get_host()}/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    def short_link_redirect(request, recipe_id):
        """
        Совершает редирект на страницу рецепта
        """
        get_object_or_404(Recipe, id=recipe_id)
        return redirect(f'/recipes/{recipe_id}')