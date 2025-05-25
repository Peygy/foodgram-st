from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe
from users.models import User


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method="favorited_method")
    is_in_shopping_cart = filters.BooleanFilter(
        method="in_shopping_cart_method"
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())

    def favorited_method(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def in_shopping_cart_method(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ("author",)

