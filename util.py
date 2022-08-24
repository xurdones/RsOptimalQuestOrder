from collections import OrderedDict
from itertools import filterfalse, tee


# https://docs.python.org/3/library/itertools.html#itertools-recipes
def partition(pred, iterable):
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


class MyOrderedDict(OrderedDict):
    def last(self):
        return next(reversed(self))