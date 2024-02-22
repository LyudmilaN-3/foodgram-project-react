from django.conf.urls import url
from django.urls import include
from rest_framework import routers

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipesViewSet,
    TagViewSet
)


app_name = 'api'

router_v1 = routers.DefaultRouter()


router_v1.register(r'users', CustomUserViewSet, basename='users')
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipesViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet)

urlpatterns = [
    url(r'^auth/', include('djoser.urls.authtoken')),
    url(r'', include(router_v1.urls)),
]
