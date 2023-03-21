from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (FavouriteRecipe, Ingredients, IngredientsRecipe,
                            Recipes, ShoppingCartRecipe, Tags)
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .serializers import (IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, TagSerializer, UserListSerializer,
                          UserSerializer, UserSubscribeSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    ordering_fields = ['cooking_time']
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        is_favourited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_favourited == '1':
            queryset = queryset.filter(
                favourited_by__user=self.request.user
            )
        if is_in_shopping_cart == '1':
            queryset = queryset.filter(
                added_to_cart_by__user=self.request.user
            )

        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()

        return queryset

    def get_serializer_context(self):
        """Используем теги и ингридиенты, уже находящиеся в БД
        для создания рецепта"""
        context = super().get_serializer_context()
        context['ingredients'] = Ingredients.objects.all()
        context['tags'] = Tags.objects.all()
        return context

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializer

        return RecipeListSerializer

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            try:
                FavouriteRecipe.objects.create(user=user, recipe=recipe)
                return Response({'message': 'Добавлено в избранное'})
            except IntegrityError:
                return Response(
                    {'error': 'Уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif request.method == 'DELETE':
            try:
                favorite = FavouriteRecipe.objects.get(
                    user=user, recipe=recipe
                )
                favorite.delete()
                return Response({'message': 'Удалено из избранного'})
            except FavouriteRecipe.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Некорректный метод запроса'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            try:
                ShoppingCartRecipe.objects.create(user=user, recipe=recipe)
                return Response({'message': 'Добавлено в список покупок'})
            except IntegrityError:
                return Response({'error': 'Уже в списке покупок'}, status=400)

        elif request.method == 'DELETE':
            shopping_cart = get_object_or_404(
                ShoppingCartRecipe, user=user, recipe=recipe
            )
            shopping_cart.delete()
            return Response({'message': 'Удалено из корзины покупок'})
        return Response(
            {'error': 'Некорректный метод запроса'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_summary = ShoppingCartRecipe.objects.filter(user=user)
        recipes_id = [cart.recipe.id for cart in shopping_cart_summary]
        ingredients_list = IngredientsRecipe.objects.filter(
            recipe__in=recipes_id
        )
        ingredient_dict = {}
        for ingredient in ingredients_list:
            name = ingredient.ingredient.name
            unit = ingredient.ingredient.measurement_unit
            amount = ingredient.amount
            if name in ingredient_dict:
                ingredient_dict[name]['amount'] += amount
            else:
                ingredient_dict[name] = {'amount': amount, 'unit': unit}

        content = '\n'.join(
            [f"{name}: {details['amount']} {details['unit']}"
             for name, details in ingredient_dict.items()]
        )
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment;'
            'filename="ShoppingCart.txt"'
        )
        return response


class IngredientsListView(viewsets.ModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    http_method_names = ['get']
    pagination_class = None


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    pagination_class = None


class UserDetailView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):

            return UserSerializer

        return UserListSerializer

    @action(methods=['GET', 'PATCH'], detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        if request.method == 'PATCH':
            user = request.user
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = UserListSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        target_user = self.get_object()
        if target_user == request.user:

            return Response(
                {'detail': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'POST':
            if Subscription.objects.filter(
                subscriber=request.user,
                target_user=target_user,
            ).exists():
                return Response(
                    {'detail': 'Подписка уже существует.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user,
                target_user=target_user
            )
            serializer = UserSubscribeSerializer(subscription.subscriber)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                subscriber=request.user,
                target_user=target_user
            ).first()
            if not subscription:
                return Response(status=status.HTTP_404_NOT_FOUND)
            subscription.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        page_followed_users = self.paginate_queryset(
            User.objects.filter(subscribers__subscriber=self.request.user)
        )
        serializer = UserSubscribeSerializer(
            page_followed_users,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
