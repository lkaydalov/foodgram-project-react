from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework import routers

from api.views import ChangePasswordView, UserDetailView

router = routers.DefaultRouter()
router.register(r'users', UserDetailView, basename='users')

urlpatterns = [
    path('auth/token/login/', TokenCreateView.as_view()),
    path('auth/token/logout/', TokenDestroyView.as_view()),
    path('users/set_password/',
         ChangePasswordView.as_view(),
         name='set_password',),
    path('', include(router.urls)),
]
