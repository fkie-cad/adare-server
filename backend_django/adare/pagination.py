from rest_framework.pagination import LimitOffsetPagination


class DefaultLimitOffsetPagination(LimitOffsetPagination):
    """Limit/offset pagination that is always on.

    Plain LimitOffsetPagination with no PAGE_SIZE skips pagination when the
    client omits ?limit and returns the whole table as a bare array. Here a
    missing limit means `default_limit` rows, and an oversized one is clamped
    to `max_limit`; the response is always the {count, next, previous,
    results} envelope, so clients page by following `next`.
    """
    default_limit = 25
    max_limit = 200
