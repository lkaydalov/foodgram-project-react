import base64

import webcolors
from django.core.files.base import ContentFile
from recipes.models import Ingredients, IngredientsRecipe, Recipes, Tags
from rest_framework import serializers
from users.models import User


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
        extra_kwargs = {'password': {'write_only': 'True'}}

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


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name',
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientsRecipe
        fields = (
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
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True,
        required=True,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            'name',
            'text',
            'image',
            'author',
            'tags',
            'ingredients',
            'cooking_time',
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data.pop('id')
            amount = ingredient_data.pop('amount')
            IngredientsRecipe.objects.create(
                ingredient=ingredient, recipe=recipe, amount=amount
            )
        for tag in tags_data:
            recipe.tags.add(tag)

        return recipe

    def update(self, instance, validated_data):
        if self.context['request'].user != instance.author:
            raise serializers.ValidationError(
                'У вас нет прав обновлять данный рецепт',
            )
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                ingredient = ingredient_data.get('id')
                amount = ingredient_data.get('amount')
                IngredientsRecipe.objects.create(
                    ingredient=ingredient, recipe=instance, amount=amount
                )

        tags_data = validated_data.pop('tags')
        if tags_data:
            instance.tags.clear()
            instance.tags.set(tags_data)

        instance.save()
        return instance


class RecipeListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    id = serializers.PrimaryKeyRelatedField(
        queryset=Recipes.objects.all(),
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField()

    def get_ingredients(self, obj):
        return IngredientRecipeSerializer(
            IngredientsRecipe.objects.filter(recipe=obj).all(),
            many=True,
        ).data

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


class UserSubscribeSerializer(UserSerializer):
    recipes = RecipeListSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

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
            'recipes_count'
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
        serializer = RecipeListSerializer(recipes, many=True, read_only=True)
        return serializer.data
