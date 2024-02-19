import base64
import webcolors
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Ingredient,
    IngredientInRecipe,
    Favorite,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import User, Subscription


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer для ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class TagSerializer(serializers.ModelSerializer):
    """Serializer для тега."""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Serializer для отображения списка ингредиентов в рецепте."""
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('amount', 'name', 'measurement_unit', 'id')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    """Serializer для кастомной модели User"""
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return Subscription.objects.filter(
                    user=user, author=obj).exists()
            if user.is_anonymous:
                return False
        return False

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )


class RecipeListSerializer(serializers.ModelSerializer):
    """Serializer для получения списка рецептов."""
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(many=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        return IngredientInRecipeSerializer(
            IngredientInRecipe.objects.filter(recipe=obj).all(), many=True
        ).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return Favorite.objects.filter(
                    user=user, recipe=obj
                ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return ShoppingCart.objects.filter(
                    user=user, recipe=obj
                ).exists()
        return False

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'is_favorited',
            'is_in_shopping_cart',
            'cooking_time'
        )


class IngredientSelectInRecipeSerializer(serializers.ModelSerializer):
    """Serializer для выбора ингредиентов при создании/обновлении рецепта."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer для создания/обновления рецепта."""
    ingredients = IngredientSelectInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=False, allow_null=True)
    author = CustomUserSerializer(many=False, required=False)

    def validate(self, data):
        name = data.get('name')
        tags = data.get('tags')
        text = data.get('text')
        image = data.get('image')
        ingredients = data.get('ingredients')
        if not name:
            raise ValidationError('Название рецепта должно быть добавлено.')
        if not tags:
            raise ValidationError('Хотя бы один тег должен быть установлен.')
        tags_data = []
        for tag in tags:
            if tag in tags_data:
                raise ValidationError('Нельзя выбрать одинаковые теги.')
            tags_data.append(tag)
        if not ingredients:
            raise ValidationError(
                'Хотя бы один ингредиент должен быть выбран.'
            )
        ingredients_data = []
        for ingredient in ingredients:
            if ingredient in ingredients_data:
                raise ValidationError('Нельзя выбрать одинаковые ингредиенты.')
            ingredients_data.append(ingredient)
        if not text:
            raise ValidationError('Добавьте описание приготовления рецепта.')
        if not image:
            raise ValidationError('Добавьте изображение.')
        return data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author_data = self.context.get('request').user
        recipe = Recipe.objects.create(author=author_data, **validated_data)
        create_ingredients = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        IngredientInRecipe.objects.bulk_create(
            create_ingredients
        )
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.clear()
        instance.tags.set(tags_data)
        if ingredients is not None:
            instance.ingredients.clear()
            create_ingredients = [
                IngredientInRecipe(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            IngredientInRecipe.objects.bulk_create(
                create_ingredients
            )
        return super().update(instance, validated_data)

    def to_representation(self, value):
        return RecipeListSerializer(value).data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeInFavoriteSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer для отображения рецептов в избранном/подписках."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    """Serializer для подписки на автора."""
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, instance):
        return instance.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request:
            user = self.context['request'].user
            if user.is_authenticated:
                return user.subscriber.filter(author=obj).exists()
            if user.is_anonymous:
                return False
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes:
            if recipes_limit and type(int(recipes_limit)) is int:
                recipes = obj.recipes.all()[:int(recipes_limit)]
        return RecipeInFavoriteSubscriptionSerializer(
            recipes, many=True, context={'request': request}).data

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'first_name',
                  'last_name',
                  'username',
                  'recipes',
                  'is_subscribed',
                  'recipes_count'
                  )


class SubscriptionGetSerializer(serializers.ModelSerializer):
    """Serializer для подписок только для GET-запросов."""

    def validate(self, data):
        user = self.context['request'].user
        author = data['author']
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError('Подписка уже существует.')
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author, context=self.context).data

    class Meta:
        model = Subscription
        fields = ('author', 'user',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer для избранных рецептов."""

    def to_representation(self, value):
        return RecipeInFavoriteSubscriptionSerializer(value.recipe).data

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer для рецептов в списке покупок."""

    def to_representation(self, value):
        return RecipeInFavoriteSubscriptionSerializer(value.recipe).data

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
