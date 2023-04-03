from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (FavouriteRecipe, Ingredients, IngredientsRecipe,
                            Recipes, ShoppingCartRecipe, Tags)
from users.models import Subscription, User
from .filters import CustomQueryFilter
from .serializers import (ChangePasswordSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeListSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserListSerializer, UserSerializer,
                          UserSubscribeListSerializer, UserSubscribeSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = CustomQueryFilter
    search_fields = ['name']
    ordering_fields = ['cooking_time']
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request):
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(author=self.request.user)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        recipe = self.get_object()
        serializer = RecipeSerializer(
            recipe,
            context={'request': request},
            data=request.data,
            partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):

            return RecipeSerializer

        return RecipeListSerializer

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            data = {'user': user.id, 'recipe': recipe.id}
            serializer = FavoriteSerializer(context={
                'recipe': recipe,
                'request': request
            }, data=data)
            if serializer.is_valid():
                serializer.save()

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            favorite = FavouriteRecipe.objects.get(
                user=user.id, recipe=recipe.id,
            )
            favorite.delete()

            return Response(
                {'message': 'Удалено из избранного'},
                status=status.HTTP_204_NO_CONTENT
            )
        except FavouriteRecipe.DoesNotExist:

            return Response(
                {'error': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        data = {'user': user.id, 'recipe': recipe.id}
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(context={
                'recipe': recipe,
                'request': request,
            }, data=data)
            if serializer.is_valid():
                serializer.save()

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            shopping_cart = get_object_or_404(
                ShoppingCartRecipe, user=user, recipe=recipe
            )
            shopping_cart.delete()

            return Response({'message': 'Удалено из корзины покупок'})
        except ShoppingCartRecipe.DoesNotExist:

            return Response(
                {'error': 'Рецепт не в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
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


class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            context={'request': request},
            data=request.data,
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(
                {"detail": "Пароль успешно изменён, поздравляем."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):

            return UserSerializer

        return UserListSerializer

    @action(methods=['GET'], detail=False,
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserListSerializer(request.user)

        return Response(serializer.data)

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, pk=None):
        target_user = self.get_object()

        if request.method == 'POST':
            serializer = UserSubscribeSerializer(context={
                'target_user': target_user,
                'request': request,
            }, data=request.data)
            if serializer.is_valid():
                serializer.save()

                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            subscription = Subscription.objects.filter(
                subscriber=request.user,
                target_user=target_user
            )
            subscription.delete()

            return Response(
                {'message': 'Удалено из подписок'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Subscription.DoesNotExist:

            return Response(
                {'error': 'Пользователь не в подписках'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        page_followed_users = self.paginate_queryset(
            User.objects.filter(subscribers__subscriber=request.user)
        )
        serializer = UserSubscribeListSerializer(
            page_followed_users,
            many=True,
            context={'request': request}
        )

        return self.get_paginated_response(serializer.data)
