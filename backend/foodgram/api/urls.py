from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import (IngredientsListView, RecipeViewSet, TagsViewSet,
                    ChangePasswordView, UserDetailView)

router = DefaultRouter()
router.register(r'users', UserDetailView, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipe')
router.register(r'ingredients', IngredientsListView, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')

urlpatterns = [
    path('auth/token/login/', TokenCreateView.as_view()),
    path('auth/token/logout/', TokenDestroyView.as_view()),
    path('users/set_password/',
         ChangePasswordView.as_view(),
         name='set_password',),
    path('', include(router.urls)),
]
