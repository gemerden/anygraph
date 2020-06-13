from collections.abc import MutableSet
from operator import attrgetter

from anygraph.tools import unique_name
from anygraph.visitors import Iterator, Visitor, Found


class DelegateSet(MutableSet):

    def __init__(self, owner, linker, get_id):
        super().__init__()
        self.targets = {}
        self.owner = owner
        self.linker = linker
        self.get_id = get_id

    def __len__(self):
        return len(self.targets)

    def __iter__(self):
        return iter(self.targets.values())

    def __contains__(self, target):
        return self.get_id(target) in self.targets

    def add(self, target):
        if target is not None and self.get_id(target) not in self.targets:
            self.linker._check(self.owner, target)
            self.linker._on_link(self.owner, target)
            self.linker._link(self.owner, target)

    def discard(self, target):
        if target is not None and self.get_id(target) in self.targets:
            self.linker._unlink(self.owner, target)
            self.linker._on_unlink(self.owner, target)

    def update(self, targets):
        for target in targets:
            self.add(target)

    def replace(self, targets):
        self.clear()
        self.update(targets)

    def _set(self, target):
        self.targets[self.get_id(target)] = target

    def _del(self, target):
        self.targets.pop(self.get_id(target), None)

    def __str__(self):
        return f"{{{', '.join(map(str, self))}}}"

    def __repr__(self):
        return f"{{{', '.join(map(repr, self))}}}"


class DelegateMap(DelegateSet):

    def __getitem__(self, key):
        return self.targets[key]

    def keys(self):
        return self.targets.keys()

    def values(self):
        return self.targets.values()

    def items(self):
        return self.targets.items()

    def get(self, key, _default=None):
        return self.targets.get(key, _default)


class DelegateNamedMap(DelegateMap):
    def add(self, target):
        self.set_name(target)
        super().add(target)

    def set_name(self, target):
        target.name = unique_name(
            space=self.targets.keys(),
            base=type(target).__name__.lower(),
            name=self.get_id(target)
        )


class BaseLinker(object):
    get_id = id  # default

    def __init__(self, target_name=None, cyclic=True, to_self=True, on_link=None, on_unlink=None, get_id=None):
        self.target_name = target_name
        self.cyclic = cyclic
        self.to_self = to_self
        self._do_on_link = on_link
        self._do_on_unlink = on_unlink
        self._get_id = get_id or self.get_id
        self.name = None

    def __set_name__(self, cls, name):
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.name]
        except KeyError:
            return self._init(obj)

    def iterate(self, start_obj, cyclic=False, breadth_first=False):
        iterator = Iterator(self.name)
        yield from iterator(start_obj, cyclic=cyclic, breadth_first=breadth_first)

    __call__ = iterate  # shortcut to iteration

    def visit(self, start_obj, on_visit, cyclic=False, breadth_first=False):
        visitor = Visitor(self.name)
        return visitor(start_obj, on_visit, cyclic=cyclic, breadth_first=breadth_first)

    def build(self, start_obj, key='__iter__'):
        build_on_visit = self._build_on_visit(key, _reg={})
        self.visit(start_obj, on_visit=build_on_visit, breadth_first=True)
        return self

    def find(self, start_obj, filter):
        return [obj for obj in self.iterate(start_obj, breadth_first=True) if filter(obj)]

    def reachable(self, start_obj, target_obj):
        iterator = Iterator(self.name)
        for obj in iterator(start_obj):
            if target_obj in iterator.iter_object(obj):
                return True
        return False

    def walk(self, start_obj, key, on_visit=None):
        yield from Iterator(self.name).walk(start_obj, key=key, on_visit=on_visit)

    def is_cyclic(self, start_obj):
        seen = set()
        cyclic = False

        def visit(obj):
            nonlocal cyclic
            obj_id = self._get_id(obj)
            if obj_id in seen:
                cyclic = True
                raise StopIteration
            seen.add(obj_id)

        self.visit(start_obj, on_visit=visit, cyclic=True)
        return cyclic

    def in_cycle(self, start_obj):
        return self.reachable(start_obj, start_obj)

    def shortest_path(self, start_obj, target_obj, get_cost=None, heuristic=None):
        return Iterator(self.name).shortest_path(start_obj, target_obj,
                                                 get_cost=get_cost,
                                                 heuristic=heuristic)

    def _reverse(self, target):
        if self.target_name is None:
            return None
        return getattr(target.__class__, self.target_name)

    def _existing(self, obj, target):
        raise NotImplementedError

    def _creates_cycle(self, obj, target):
        if obj is target:
            return True
        if self.name == self.target_name:
            return True
        if target is None:
            return False
        if self._existing(obj, target):
            return False
        return self.reachable(target, obj)

    def _check(self, obj, target):
        if target is None:
            return
        reverse = self._reverse(target)
        if not (self.to_self and (not reverse or reverse.to_self)):  # reverse might be a different relationship
            if obj is target:
                raise ValueError(f"pointing '{self.name}' in {obj.__class__.__name__} back to self: 'to_self' is set to False")
        if not (self.cyclic and (not reverse or reverse.cyclic)):
            if self._creates_cycle(obj, target):
                raise ValueError(f"setting '{self.name}' in {obj.__class__.__name__} creates cycle: 'cyclic' is set to False")

    def _link(self, obj, target):
        self._set(obj, target)
        if self.target_name:
            self._reverse(target)._set(target, obj)

    def _unlink(self, obj, target=None):
        if target is not None:
            if self.target_name:
                self._reverse(target)._del(target, obj)
            self._del(obj, target)

    def _on_link(self, obj, target, _remote=False):
        if self._do_on_link:
            return self._do_on_link(obj, target)
        if self.target_name and not _remote:
            return self._reverse(target)._on_link(target, obj, True)

    def _on_unlink(self, obj, target, _remote=False):
        if self._do_on_unlink:
            return self._do_on_unlink(obj, target)
        if self.target_name and not _remote:
            return self._reverse(target)._on_unlink(target, obj, True)

    def _init(self, obj):
        raise NotImplementedError

    def _set(self, obj, value):
        raise NotImplementedError

    def _del(self, obj, target):
        raise NotImplementedError

    def _build_on_visit(self, key, _reg):
        raise NotImplementedError


class One(BaseLinker):

    def __set__(self, obj, target):
        self._check(obj, target)
        self._unlink(obj)
        if target is not None:
            if self.target_name:
                self._reverse(target)._unlink(target)
            self._on_link(obj, target)
            self._link(obj, target)

    def __delete__(self, obj):
        target = self.__get__(obj)
        self._unlink(obj, target)
        self._on_unlink(obj, target)

    def _existing(self, obj, target):
        return target is not None and self.__get__(obj) is target

    def _build_on_visit(self, key, _reg):
        get_id = self._get_id

        def visit(obj):
            if callable(key):
                value = key(obj)
            else:
                value = getattr(obj, key)
            ident = get_id(value)
            if ident in _reg:
                value = _reg[ident]
            else:
                _reg[ident] = value
            setattr(obj, self.name, value)
        return visit

    def _init(self, obj):
        obj.__dict__[self.name] = None

    def _set(self, obj, target):
        obj.__dict__[self.name] = target

    def _del(self, obj, target):
        obj.__dict__[self.name] = None

    def _unlink(self, obj, target=None):
        if target is None:
            target = self.__get__(obj)
        super()._unlink(obj, target)


class BaseMany(BaseLinker):
    many_class = None

    def __set__(self, obj, targets):
        self.__get__(obj).replace(targets)

    def __delete__(self, obj):
        self.__get__(obj).clear()

    def _existing(self, obj, target):
        return target is not None and target in self.__get__(obj)

    def _build_on_visit(self, key, _reg):
        get_id = self._get_id

        def visit(obj, key=key):
            if isinstance(key, str):
                key = getattr(obj.__class__, key)
            for value in key(obj):
                ident = get_id(value)
                if ident in _reg:
                    value = _reg[ident]
                else:
                    _reg[ident] = value
                getattr(obj, self.name).add(value)
        return visit

    def _init(self, obj):
        delegate = obj.__dict__[self.name] = self.many_class(obj, linker=self, get_id=self._get_id)
        return delegate

    def _set(self, obj, target):
        self.__get__(obj)._set(target)

    def _del(self, obj, target):
        self.__get__(obj)._del(target)


class Many(BaseMany):
    many_class = DelegateSet


class ManyMap(BaseMany):
    many_class = DelegateMap


class ManyNamed(BaseMany):
    get_id = attrgetter('name')
    many_class = DelegateNamedMap


if __name__ == '__main__':
    pass
