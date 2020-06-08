from collections.abc import MutableSet
from operator import attrgetter

from anygraph.visitors import Iterator, Visitor


class DelegateSet(MutableSet):
    get_id = id

    def __init__(self, owner, linker):
        super().__init__()
        self.targets = {}
        self.owner = owner
        self.linker = linker

    def __len__(self):
        return len(self.targets)

    def __iter__(self):
        return iter(self.targets.values())

    def __contains__(self, target):
        return self.get_id(target) in self.targets

    def add(self, target):
        if self.get_id(target) not in self.targets:
            self.linker.on_link(self.owner, target)
            self.linker.link(self.owner, target)

    def discard(self, target):
        if self.get_id(target) in self.targets:
            self.linker.unlink(self.owner, target)
            self.linker.on_unlink(self.owner, target)

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
    get_id = attrgetter('name')

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

    def __init__(self, target_name, on_link=None, on_unlink=None):
        self.target_name = target_name
        self._on_link = on_link
        self._on_unlink = on_unlink
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

    def iterate(self, start_obj, repeat=False, breadth_first=False):
        iterator = Iterator(self.name, repeat=repeat)
        yield from iterator.iterate(start_obj, breadth_first=breadth_first)

    def visit(self, start_obj, on_visit, repeat=False, breadth_first=False):
        visitor = Visitor(self.name, repeat=repeat)
        return visitor(start_obj, on_visit, breadth_first=breadth_first)

    def other(self, target):
        return getattr(target.__class__, self.target_name)

    def on_link(self, obj, target, _remote=False):
        if self._on_link:
            return self._on_link(obj, target)
        if not _remote:
            return self.other(target).on_link(target, obj, True)

    def on_unlink(self, obj, target, _remote=False):
        if self._on_unlink:
            return self._on_unlink(obj, target)
        if not _remote:
            return self.other(target).on_unlink(target, obj, True)

    def link(self, obj, target):
        self.other(target)._set(target, obj)
        self._set(obj, target)

    def unlink(self, obj, target=None):
        if target is not None:
            self.other(target)._del(target, obj)
            self._del(obj, target)

    def _init(self, obj):
        raise NotImplementedError

    def _set(self, obj, value):
        raise NotImplementedError

    def _del(self, obj, target):
        raise NotImplementedError


class One(BaseLinker):

    def __set__(self, obj, target):
        self.unlink(obj)
        if target is not None:
            self.other(target).unlink(target)
            self.on_link(obj, target)
            self.link(obj, target)

    def __delete__(self, obj):
        target = self.__get__(obj)
        self.unlink(obj, target)
        self.on_unlink(obj, target)

    def _init(self, obj):
        obj.__dict__[self.name] = None

    def _set(self, obj, target):
        obj.__dict__[self.name] = target

    def _del(self, obj, target):
        obj.__dict__[self.name] = None

    def unlink(self, obj, target=None):
        if target is None:
            target = self.__get__(obj)
        super().unlink(obj, target)



class BaseMany(BaseLinker):
    many_class = None

    def __set__(self, obj, targets):
        self.__get__(obj).replace(targets)

    def __delete__(self, obj):
        self.__get__(obj).clear()

    def _init(self, obj):
        delegate = obj.__dict__[self.name] = self.many_class(obj, linker=self)
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
    many_class = DelegateNamedMap


if __name__ == '__main__':
    pass
