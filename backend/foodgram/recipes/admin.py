from django.contrib import admin

from users.models import Subscription, User
from .models import (FavouriteRecipe, Ingredients, IngredientsRecipe, Recipes,
                     ShoppingCartRecipe, Tags)


class UserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'username',)


class IngredientsRecipeInline(admin.TabularInline):
    model = IngredientsRecipe
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count')
    list_filter = ('name', 'author', 'tags',)
    readonly_fields = ('favorite_count',)
    inlines = (IngredientsRecipeInline,)

    def favorite_count(self, obj):
        return obj.favourited_by.count()
    favorite_count.short_description = "Число добавлений в избранное"


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
