import random
from collections import deque
from heapq import heappop, heappush
from operator import attrgetter


class Found(Exception):
    def __init__(self, what):
        self.what = what


class BaseIterator(object):

    def __init__(self, attr_name, raise_on_missing=False):
        self.getter = attrgetter(attr_name)
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

    def iterate(self, obj, cyclic=False, breadth_first=False):
        registry = None if cyclic else set()
        if breadth_first:
            yield from self._breadth_first(obj, reg=registry)
        else:
            yield from self._depth_first(obj, reg=registry)

    __call__ = iterate

    def _depth_first(self, obj, reg):
        """ does not use recursion to prevent running out of the callstack """
        if reg is not None:
            reg.add(id(obj))
        stack = [obj]
        while len(stack):
            obj = stack.pop()
            yield obj
            objs = list(self.iter_object(obj))
            if reg is None:
                stack.extend(reversed(objs))
            else:
                for next_obj in reversed(objs):
                    if id(next_obj) not in reg:
                        reg.add(id(next_obj))
                        stack.append(next_obj)

    def _breadth_first(self, obj, reg):
        if reg is not None:
            reg.add(id(obj))
        queue = deque([obj])
        while len(queue):
            obj = queue.popleft()
            yield obj
            for next_obj in self.iter_object(obj):
                if reg is None:
                    queue.append(next_obj)
                else:
                    if id(next_obj) not in reg:
                        reg.add(id(next_obj))
                        queue.append(next_obj)

    def shortest_path(self, start_obj, target_obj, get_cost=None, heuristic=None):
        if get_cost is None:
            def get_cost(o1, o2):
                return 0 if o1 is o2 else 1
        if heuristic:
            return self._astar(start_obj, target_obj, get_cost, heuristic)
        else:
            return self._dijkstra(start_obj, target_obj, get_cost)

    def walk(self, start_obj, key, on_visit=None):
        obj = start_obj
        while True:
            if on_visit:
                on_visit(obj)
            yield obj
            obj = min(self.iter_object(obj), key=key)

    def _dijkstra(self, start_obj, target_obj, get_cost):
        """
            Pretty standard implementation of Dijkstra, id() is used because not all objects are hashable and
            the implementation uses a set and dicts.
        """
        path = {id(start_obj): None}
        cost = {id(start_obj): 0}
        queue = deque([start_obj])
        done = {}  # a dict because it is also used to translate back from ids to objects in _create_path
        while len(queue):
            obj = queue.popleft()
            obj_id = id(obj)
            done[obj_id] = obj

            if obj is target_obj:
                return self._create_path(obj, path, id_map=done)

            for next_obj in self.iter_object(obj):
                next_id = id(next_obj)
                if next_id in done:
                    continue

                next_cost = cost[obj_id] + get_cost(obj, next_obj)
                if next_cost >= cost.get(next_id, float('inf')):
                    continue

                path[next_id] = obj_id
                cost[next_id] = next_cost
                queue.append(next_obj)
        return None  # there is no path

    def _astar(self, start_obj, target_obj, get_cost, heuristic):
        """
            Pretty standard implementation of Astar, id() is used because not all objects are hashable and
            the implementation uses a set and dicts.
        """
        path = {id(start_obj): None}
        cost = {id(start_obj): 0}
        heap = [(None, id(start_obj), start_obj)]
        done = {}  # a dict because it is also used to translate back from ids to objects in _create_path
        while heap:
            _, obj_id, obj = heappop(heap)
            done[obj_id] = obj

            if obj is target_obj:
                return self._create_path(obj, path, id_map=done)

            for next_obj in self.iter_object(obj):
                next_id = id(next_obj)
                if next_id in done:
                    continue

                next_cost = cost[obj_id] + get_cost(obj, next_obj)
                if next_cost >= cost.get(next_id, float('inf')):
                    continue

                from_cost = heuristic(next_obj, target_obj)

                path[next_id] = obj_id
                cost[next_id] = next_cost
                heappush(heap, (next_cost + from_cost, next_id, next_obj))  # next_id because obj's do not always have '<' operator
        return None  # there is no path

    def _create_path(self, obj, id_path, id_map):
        rev_path = []
        obj_id = id(obj)
        while obj_id is not None:
            rev_path.append(id_map[obj_id])
            obj_id = id_path[obj_id]
        return list(reversed(rev_path))


class Iterator(BaseIterator):
    pass


class Visitor(BaseIterator):

    def __call__(self, obj, on_visit, cyclic=False, breadth_first=False):
        try:
            for obj in self.iterate(obj, cyclic, breadth_first):
                on_visit(obj)
        except StopIteration:
            pass
        except Found as found:
            return found.what
        return on_visit


class BaseVisitor(BaseIterator):

    def get_store(self):
        return None

    def __call__(self, obj, cyclic=False, breadth_first=False):
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
        super().__init__(prop_name)
        self.filter = filter

    def get_store(self):
        return []

    def visit(self, obj, store):
        if self.filter(obj):
            store.append(obj)


class BaseFinder(object):
    def __init__(self, prop_name, filter):
        super().__init__(prop_name, cyclic=False)
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


class GetEndpoints(BaseVisitor):

    def get_store(self):
        return []

    def visit(self, obj, store):
        if not list(self.iter_object(obj)):
            store.append(obj)


