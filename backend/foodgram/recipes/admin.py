from django.contrib import admin

from users.models import Subscription, User
from .models import (FavouriteRecipe, Ingredients, IngredientsRecipe, Recipes,
                     ShoppingCartRecipe, Tags)


class UserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'username',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count')
    list_filter = ('name', 'author', 'tags',)

    def favorite_count(self, obj):
        return obj.favourited_by.count()


class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(User, UserAdmin)
admin.site.register(Recipes, RecipeAdmin)
admin.site.register(Ingredients, IngridientAdmin)
admin.site.register(Tags)
admin.site.register(IngredientsRecipe)
admin.site.register(FavouriteRecipe)
admin.site.register(ShoppingCartRecipe)
admin.site.register(Subscription)
