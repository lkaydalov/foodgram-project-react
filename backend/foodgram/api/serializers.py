import base64
import webcolors

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (FavouriteRecipe, Ingredients, IngredientsRecipe,
                            Recipes, ShoppingCartRecipe, Tags)
from users.models import Subscription, User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError('Недопустимо '
                                              'использовать такое имя')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('Пользователь с таким username '
                                              'уже существует')
        return username

    def validate_email(self, email):
        if User.objects.filter(email=email):
            raise serializers.ValidationError('Пользователь с таким email '
                                              'уже существует')
        return email


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)
    current_password = serializers.CharField(min_length=8, write_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        current_password = self.initial_data['current_password']
        new_password = self.initial_data['new_password']

        if current_password == new_password:
            raise serializers.ValidationError(
                'Новый пароль должен отличаться от старого пароля'
            )

        if not user.check_password(current_password):
            raise serializers.ValidationError('Неверный пароль')

        user.set_password(new_password)
        user.save()

        return user


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):

        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')

        return data


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tags
        fields = ('id', 'name', 'color', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeListSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name',
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
    )
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
    )

    class Meta:
        model = IngredientsRecipe
        fields = (
            'id',
            'amount',
            'name',
            'measurement_unit',
        )


class IngredientRecipeCreateSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(write_only=True, min_value=1)
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('recipe', 'amount', 'id')


class RecipeSerializer(serializers.ModelSerializer):
    # author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'name',
            'text',
            'image',
            # 'author',
            'tags',
            'ingredients',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Недопустимо создавать рецепт без указания ингредиентов'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Недопустимо создавать рецепт без указания тега',
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)

        self._save_ingredients(recipe, ingredients_data)
        for tag in tags_data:
            recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        if self.context['request'].user != instance.author:
            raise serializers.ValidationError(
                'У вас нет прав обновлять данный рецепт',
            )
        print(instance)
        print(validated_data)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self._save_ingredients(instance, ingredients_data)

        tags_data = validated_data.pop('tags')
        if tags_data:
            instance.tags.clear()
            instance.tags.set(tags_data)

        instance.save()
        return instance

    def _save_ingredients(self, recipe, ingredients_data):
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data.get('id')
            amount = ingredient_data.get('amount')
            IngredientsRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeListSerializer(
        source='ingredients_recipe',
        many=True,
    )
    id = serializers.PrimaryKeyRelatedField(
        queryset=Recipes.objects.all(),
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    def get_is_favorited(self, instance):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return instance.favourited_by.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, instance):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return instance.added_to_cart_by.filter(user=request.user).exists()
        return False

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'text',
            'author',
            'tags',
            'ingredients',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
        )


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeListSerializer(many=True, required=False)
    id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'recipes',
        )
        extra_kwargs = {'password': {'write_only': 'True'}}

    def get_is_subscribed(self, instance):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return instance.subscribers.filter(
                subscriber=request.user
            ).exists()
        return False


class FavoriteSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', required=False)

    class Meta:
        model = FavouriteRecipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context.get('recipe')
        if FavouriteRecipe.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в избранном'}
            )
        return FavouriteRecipe.objects.create(user=user, recipe=recipe)


class ShoppingCartSerializer(serializers.ModelSerializer):

    id = serializers.ReadOnlyField(source='recipe.id', required=False)
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', required=False)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', required=False)

    class Meta:
        model = ShoppingCartRecipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def create(self, validated_data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        if ShoppingCartRecipe.objects.filter(
            user=user,
            recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в списке покупок'},
            )
        return ShoppingCartRecipe.objects.create(user=user, recipe=recipe)


class UserSubscribeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='target_user.id')
    email = serializers.EmailField(
        source='target_user.email',
        required=False
    )
    username = serializers.CharField(
        source='target_user.username',
        required=False
    )
    first_name = serializers.CharField(
        source='target_user.first_name',
        required=False)
    last_name = serializers.CharField(
        source='target_user.last_name',
        required=False,
        )
    recipes = RecipeListSerializer(
        source='target_user.recipes',
        many=True,
        read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    subscriber = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    target_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = (
            'subscriber',
            'target_user',
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = ('__all__',)
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('subscriber', 'target_user')
            )
        ]

    def create(self, validated_data):
        target_user = self.context.get('target_user')
        user = self.context.get('request').user
        if target_user == user:
            raise serializers.ValidationError(
                {'error': 'Нельзя подписаться на самого себя'}
            )
        if Subscription.objects.filter(
            subscriber=user,
            target_user=target_user
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Подписка уже существует'}
            )
        return Subscription.objects.create(
            subscriber=user,
            target_user=target_user
        )

    def get_is_subscribed(*args):
        return True

    def get_recipes_count(self, obj):
        return obj.target_user.recipes.count()


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url)


class UserSubscribeListSerializer(UserSerializer):

    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = '__all__',

    def get_is_subscribed(*args):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(
            recipes,
            context={'request': request},
            many=True
        )
        return serializer.data
