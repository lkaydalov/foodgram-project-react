from api.views import UserDetailView
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', UserDetailView, basename='users')

urlpatterns = [
    path('auth/token/login/', TokenCreateView.as_view()),
    path('auth/token/logout/', TokenDestroyView.as_view()),
    path('', include(router.urls)),
]
