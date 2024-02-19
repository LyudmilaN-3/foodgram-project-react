from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from api.validators import username_validation, pattern_validation


class User(AbstractUser):
    """Кастомный класс пользователя."""
    email = models.EmailField(
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        unique=True,
        verbose_name='Юзернейм пользователя',
        validators=[
            username_validation,
            pattern_validation
        ]
    )
    first_name = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        verbose_name='Имя пользователя'
    )
    last_name = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        verbose_name='Фамилия пользователя'
    )
    password = models.CharField(
        max_length=settings.MAX_LENGTH_USERNAME,
        verbose_name='Пароль'
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Промежуточная Model подписок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписант'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f' Подписка пользователя {self.user}'
