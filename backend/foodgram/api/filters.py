import django_filters as filters

from recipes.models import Recipes


class CustomQueryFilter(filters.FilterSet):

    tags = filters.CharFilter()

    class Meta:
        model = Recipes
        fields = ['tags']

    def filter_queryset(self, queryset):
        if self.request.user.is_authenticated:
            is_favorited = self.request.query_params.get('is_favorited')
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart'
            )
            tags = self.request.query_params.getlist('tags')
            author_param = self.request.query_params.get('author')
            if author_param:
                queryset = queryset.filter(author__id=author_param)
            if is_favorited:
                queryset = queryset.add_your_annotations(
                    self.request.user
                ).filter(is_favorited=1)
            if is_in_shopping_cart:
                queryset = queryset.add_your_annotations(
                    self.request.user
                ).filter(is_in_shopping_cart=1)
            if tags:

                return queryset.filter(tags__slug__in=tags).distinct()
        tags = self.request.query_params.getlist('tags')
        if tags:

            return queryset.filter(tags__slug__in=tags).distinct()

        return queryset
