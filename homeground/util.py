
class Itercount:
    _count = 0
    _iterable = None

    def __init__(self, iterable):
        self._iterable = iterable

    def __iter__(self):
        return self

    def __next__(self):
        value = next(self._iterable)
        self._count += 1

        return value

    def count(self):
        return self._count
