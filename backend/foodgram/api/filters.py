import django_filters as filters

from recipes.models import Recipes


class CustomQueryFilter(filters.FilterSet):

    tags = filters.CharFilter()

    class Meta:
        model = Recipes
        fields = ['tags']

    def filter_queryset(self, queryset):
        user = self.request.user
        queryset = queryset.add_your_annotations(user=user)
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        tags = self.request.query_params.getlist('tags')
        if is_favorited == '1':
            queryset = queryset.filter(favourited_by__user=user)
        if is_in_shopping_cart == '1':
            queryset = queryset.filter(added_to_cart_by__user=user)
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()

        return queryset
