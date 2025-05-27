from django.contrib import admin
from recipes.models import Ingredient, Recipe, RecipeIngredients


class RecipeIngredientsInLine(admin.TabularInline):
    model = RecipeIngredients
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "text", "pub_date", "author")
    search_fields = ("name", "author")
    inlines = (RecipeIngredientsInLine,)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
