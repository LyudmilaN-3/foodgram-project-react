from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    Ingredient,
    IngredientInRecipe,
    Recipe,
    Tag,
    Favorite,
    ShoppingCart
)

admin.site.site_header = 'Администрирование проекта "Фудграм"'

admin.site.empty_value_display = 'Не задано'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_editable = (
        'name',
        'measurement_unit',
    )
    list_display_links = ('id',)
    search_fields = ('name__startwith',)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


class FavoriteInline(admin.TabularInline):
    model = Favorite
    list_display = (
        'user',
    )
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = (
        IngredientInRecipeInline,
        FavoriteInline,
        ShoppingCartInline,
    )
    list_display = (
        'id',
        'name',
        'author',
        'text',
        'pub_date',
        'short_image',
        'cooking_time',
        'favorites_count',
    )
    list_editable = (
        'name',
        'text',
        'cooking_time',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )
    list_display_links = ('id',)
    fields = [('name', 'author', 'image',),
              ('text', 'cooking_time',), ]

    @admin.display(description='Картинка')
    def short_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src={obj.image.url} width="80" height="60"'
            )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorites_count=Count('favorited'),)
        return queryset

    @admin.display(description='Количество добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorites_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_display_links = (
        'user',
    )
    list_filter = (
        'user',
    )
    search_fields = (
        'user',
        'recipe',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_display_links = (
        'user',
    )
    list_filter = (
        'user',
    )
    search_fields = (
        'user',
        'recipe',
    )
