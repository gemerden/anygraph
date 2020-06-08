from collections import deque
from operator import attrgetter


class BaseIterator(object):

    def __init__(self, attr_name, repeat=False, raise_on_missing=False):
        self.getter = attrgetter(attr_name)
        self.repeat = repeat
        self.raise_on_missing = raise_on_missing

    def iter_object(self, obj):
        try:
            attr = self.getter(obj)
        except AttributeError:
            if self.raise_on_missing:
                raise
        else:
            if attr is not None:
                try:
                    yield from attr
                except TypeError:
                    yield attr

    def iterate(self, obj, breadth_first=False):
        registry = None if self.repeat else set()
        if breadth_first:
            yield from self._breadth_first_propagate(obj, reg=registry)
        else:
            yield from self._depth_first_propagate(obj, reg=registry)

    def _depth_first_propagate(self, obj, reg):
        if not self.repeat:
            if id(obj) in reg:
                return
            reg.add(id(obj))
        yield obj
        propagate = self._depth_first_propagate
        for next_obj in self.iter_object(obj):
            yield from propagate(next_obj, reg)

    def _breadth_first_propagate(self, obj, reg):
        queue = deque([obj])
        if self.repeat:
            while len(queue):
                obj = queue.popleft()
                yield obj
                for next_obj in self.iter_object(obj):
                    queue.append(next_obj)
        else:
            reg.add(obj)
            while len(queue):
                obj = queue.popleft()
                yield obj
                for next_obj in self.iter_object(obj):
                    if id(next_obj) not in reg:
                        reg.add(id(next_obj))
                        queue.append(next_obj)


class Iterator(BaseIterator):
    pass


class Visitor(BaseIterator):

    def __call__(self, obj, on_visit, breadth_first=False):
        try:
            for obj in self.iterate(obj, breadth_first):
                on_visit(obj)
        except StopIteration:
            pass
        return on_visit


class BaseVisitor(BaseIterator):

    def get_store(self):
        return None

    def __call__(self, obj, breadth_first=False):
        visit = self.visit
        store = self.get_store()
        try:
            for obj in self.iterate(obj, breadth_first):
                result = visit(obj, store)
                if result is not None:
                    return self.post_process(result)
        except StopIteration:
            pass
        return self.post_process(store)

    def visit(self, obj, store):
        raise NotImplementedError

    def post_process(self, store):
        return store


class Gather(BaseVisitor):
    def __init__(self, prop_name, filter=lambda obj: True):
        super().__init__(prop_name, repeat=False)
        self.filter = filter

    def get_store(self):
        return []

    def visit(self, obj, store):
        if self.filter(obj):
            store.append(obj)


class BaseFinder(object):
    def __init__(self, prop_name, filter):
        super().__init__(prop_name, repeat=False)
        self.filter = filter


class Has(BaseFinder, BaseIterator):

    def __call__(self, obj, breadth_first=False):
        return any(map(self.filter, self.iterate(obj, breadth_first)))


class Find(BaseFinder, BaseVisitor):

    def get_store(self):
        return []

    def visit(self, obj, store):
        if self.filter(obj):
            store.append(obj)


class FindOne(BaseFinder, BaseVisitor):

    def visit(self, obj, store):
        if self.filter(obj):
            return obj


class IsCyclic(BaseIterator):

    def __call__(self, obj):
        temp = set()
        for obj in self.iterate(obj):
            if id(obj) in temp:
                return True
            temp.add(id(obj))
        return False


class GetEndpoints(BaseVisitor):

    def get_store(self):
        return []

    def visit(self, obj, store):
        if not list(self.iter_object(obj)):
            store.append(obj)


