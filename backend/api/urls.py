from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import IngredientViewSet, RecipeViewSet
from users.views import AppUserViewSet

router = DefaultRouter()
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)
router.register("users", AppUserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
