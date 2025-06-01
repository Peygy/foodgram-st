from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipes.views import RecipeViewSet

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    # NOTE: Планировал перенести в api.urls, но
    # возникла проблема с редиректом на короткую ссылку
    # через путь localhost/s/...
    path("s/<int:recipe_id>/",
         RecipeViewSet.short_link_redirect,
         name='short-link-redirect'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
