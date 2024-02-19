import re

from rest_framework import serializers


def username_validation(value):
    """Проверка на наличие в юзернейм пользователя me."""
    if value.lower() == 'me':
        raise serializers.ValidationError('Недопустимое имя пользователя.')


def pattern_validation(value):
    """Проверка соответствия паттерну."""
    pattern = r'^[a-zA-Z][a-zA-Z0-9-_\.]{1,20}$'
    if re.search(pattern, value) is None:
        invalid_symbols = [symbol for symbol in value
                           if not re.match(pattern, symbol)]
        raise serializers.ValidationError(
            'Недопустимые символы:'
            f'{", ".join(invalid_symbols)}'
        )
