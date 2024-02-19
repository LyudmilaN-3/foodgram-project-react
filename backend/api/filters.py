from django_filters.filters import AllValuesMultipleFilter, NumberFilter
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    """FilterSet для выбора ингредиентов."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """FilterSet для рецептов: по тегам, авторам,
    вхождению в избранное и в список покупок."""
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    author = NumberFilter(field_name='author__id')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_in_shopping_cart', 'is_favorited')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод фильтрации по вхождению в список покупок."""
        user = self.request.user
        if not user.is_authenticated or not value:
            return queryset
        return queryset.filter(list_of_shopping__user=user)

    def filter_is_favorited(self, queryset, name, value):
        """Метод фильтрации по вхождению в список избранного."""
        user = self.request.user
        if not user.is_authenticated or not value:
            return queryset
        return queryset.filter(favorited__user=user)
