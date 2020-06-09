import random
from contextlib import contextmanager
from heapq import heappop, heappush, heappushpop, heapreplace, heapify
from time import perf_counter
from types import MethodType


def unique_name(space, base, name=None):
    if not name or name in space:
        base = strip_number(name or base)
        name, num = f"{base}_0", 0
        while name in space:
            num += 1
            name = f"{base}_{num}"
    return name


def strip_number(name, sep='_'):
    base, _, num = name.rpartition(sep)
    try:
        int(num)
    except ValueError:
        return name
    else:
        return base


def flipcoin(prob=0.5):
    return random.random() < prob


def chained(iterable, n=2):
    sequence = list(iterable)
    c = len(sequence) - n + 1
    return zip(*(sequence[i:c + i] for i in range(n)))


@contextmanager
def stopwatch(timer=perf_counter):
    """ do not call lambda within context = with-block, this raises a NameError """
    t = timer()
    yield lambda: delta
    delta = timer() - t  # fixed on context exit


def bind_builtin_to_instance(obj, **builtin_funcs):
    for name, func in builtin_funcs.items():
        setattr(obj, name, MethodType(func, obj))


class Heap(list):
    append = None
    insert = None
    extend = None
    __setitem__ = None
    __delitem__ = None

    bind = bind_builtin_to_instance

    def __init__(self, iterable=()):
        self.bind(pop=heappop,
                  push=heappush,
                  pushpop=heappushpop,
                  replace=heapreplace)
        super().__init__(iterable)
        heapify(self)
