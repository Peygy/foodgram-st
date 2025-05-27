from django.contrib import admin
from django.urls import include, path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from recipes.models import Recipe
from recipes.views import IngredientViewSet, RecipeViewSet
from users.views import CustomUserViewSet

router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)
router.register("users", CustomUserViewSet, basename="users")

def short_link_redirect(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    detail_url = reverse('recipe-detail', kwargs={'pk': recipe.id})
    detail_url = f'/recipes/{recipe_id}/'
    return redirect(detail_url)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("djoser.urls.authtoken")),
    path("s/<int:recipe_id>/", short_link_redirect, name='short-link-redirect'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
