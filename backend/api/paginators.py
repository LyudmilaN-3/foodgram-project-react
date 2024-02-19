from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Класс кастомной пагинации."""
    page_size_query_param = 'limit'
