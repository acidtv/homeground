
class Itercount:
    """
    A wrapper for an iterable to count the number of iterations without
    turning the iterator into a list.

    Sample usage:
    >>> range_count = Itercount(iter(range(10)))
    >>> r = functools.reduce(lambda: a, b: a+b, range_count)
    >>> range_count.count()
    10
    """
    _count = 0
    _iterable = None

    def __init__(self, iterable):
        self._iterable = iterable

    def __iter__(self):
        return self

    def __next__(self):
        """Return next value in iterator and increase the count with 1"""
        value = next(self._iterable)
        self._count += 1

        return value

    def count(self):
        """Return the number of iterations so far"""
        return self._count
