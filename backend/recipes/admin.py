from django.contrib import admin
from django.db.models import Count

from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredients


class RecipeIngredientsInLine(admin.TabularInline):
    model = RecipeIngredients
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "author", "pub_date", "favorite_count")
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("pub_date",)
    inlines = (RecipeIngredientsInLine,)

    def get_queryset(self, request):
        """
        Переопределение queryset для добавления подсчета избранных
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _favorite_count=Count("favorite", distinct=True)
        )
        return queryset

    def favorite_count(self, obj):
        """
        Отображение количества добавлений рецепта в избранное
        """
        return obj._favorite_count
    favorite_count.admin_order_field = '_favorite_count'
    favorite_count.short_description = 'В избранном'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
