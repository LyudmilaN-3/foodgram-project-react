from django.contrib import admin
from django.db.models import Count
from users.models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'password',
        'subscribers_count',
        'recipes_count',
    )
    list_editable = ('password',)
    list_display_links = ('username',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            recipes_count=Count('recipes'),
            subscribers_count=Count('following')
        )
        return queryset

    @admin.display(description='Количество подписок')
    def subscribers_count(self, obj):
        return obj.subscribers_count

    @admin.display(description='Количество рецептов')
    def recipes_count(self, obj):
        return obj.recipes_count


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
