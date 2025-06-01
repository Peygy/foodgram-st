from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """
    Набор фильтров для Recipe
    """
    is_favorited = filters.BooleanFilter(method="favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="in_shopping_cart")

    class Meta:
        model = Recipe
        fields = (
            "author",
        )

    def favorited(self, queryset, name, value):
        """
        Фильтрует рецепты по статусу избранного для пользователя
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        if value and not self.request.user.is_authenticated:
            return queryset.none()
        return queryset

    def in_shopping_cart(self, queryset, name, value):
        """
        Фильтрует рецепты по статусу нахождения
        в списке покупок для пользователя
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_list__user=self.request.user
            )
        if value and not self.request.user.is_authenticated:
            return queryset.none()
        return queryset


class IngredientFilter(FilterSet):
    """
    Набор фильтров для Ingredient
    """
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = (
            "name",
        )
