from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """
    Paginator с возможностью установки лимита
    на количество элементов на странице
    """
    page_size = 6
    page_size_query_param = "limit"
    max_page_size = 100
