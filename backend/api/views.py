from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter, IngredientFilter
from .serializers import (
    IngredientSerializer,
    FavoriteSerializer,
    RecipeListSerializer,
    TagSerializer,
    RecipeCreateUpdateSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    SubscriptionGetSerializer
)
from .permissions import IsAuthorOrReadOnly
from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Recipe,
    Tag,
    ShoppingCart
)
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    """ViewSet для работы с пользователями."""
    permission_classes = (AllowAny,)

    @action(
        methods=['get', ],
        url_path='me',
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        user = self.request.user
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionGetSerializer(
            data={
                'author': author.id,
                'user': user.id
            },
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        user = self.request.user
        author = get_object_or_404(User, id=id)
        obj = Subscription.objects.filter(user=user, author=author)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get', ],
        detail=False,
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitOffsetPagination,
    )
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=request.user)
        authors_paginate = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            authors_paginate,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet для ингредиентов только для GET-запросов."""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = (IngredientFilter)
    search_fields = ('^name', '=name')


class TagViewSet(ReadOnlyModelViewSet):
    """ViewSet для тегов только для GET-запросов."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class RecipesViewSet(ModelViewSet):
    """ViewSet для рецептов."""
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = (RecipeFilter)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update',):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        qs = Recipe.objects.all()
        author = self.request.query_params.get('author', None)
        if author:
            qs = qs.filter(author=author)
        return qs

    @action(
        methods=['post', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        user = self.request.user
        if not Recipe.objects.filter(pk=pk):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = Recipe.objects.get(pk=pk)
        if Favorite.objects.filter(recipe=recipe, user=user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteSerializer(
            data={
                'recipe': recipe.id,
                'user': user.id
            },
            context={
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe_obj = Favorite.objects.filter(user=user, recipe=recipe)
        if recipe_obj.exists():
            recipe_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', ],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        user = self.request.user
        if not Recipe.objects.filter(pk=pk):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        recipe = Recipe.objects.get(pk=pk)
        if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = ShoppingCartSerializer(
            data={
                'recipe': recipe.id,
                'user': user.id
            },
            context={
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get', ],
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__list_of_shopping__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by(
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        text = ''
        for index, row in enumerate(ingredients, 1):
            text += (f'{index} - {row["ingredient__name"]}  '
                     f'{row["total_amount"]}  '
                     f'{row["ingredient__measurement_unit"]}\n')
        return HttpResponse(text, content_type='text/plain')

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe_obj = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if recipe_obj.exists():
            recipe_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
