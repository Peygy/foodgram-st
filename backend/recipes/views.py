from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def short_link_redirect_view(request, recipe_id):
    """
    Совершает редирект на страницу рецепта по короткой ссылке.
    """
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}')
