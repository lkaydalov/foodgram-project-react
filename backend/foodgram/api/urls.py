from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientsListView, RecipeViewSet, TagsViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientsListView, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('users.urls')),
    path(r'', include('djoser.urls')),
]
