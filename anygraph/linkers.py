from collections import deque
from collections.abc import Set, Mapping
from functools import partial, wraps

from anygraph.tools import unique_name, save_graph_image
from anygraph.visitors import Iterator, Visitor


class BaseDelegate(object):

    def __init__(self, owner, linker):
        super().__init__()
        self.targets = {}
        self.owner = owner
        self.linker = linker

    def __len__(self):
        return len(self.targets)

    def include(self, *targets):
        """ adds and connects targets to the object owning this instance (self.owner) """
        for target in targets:
            if target is not None and target not in self.targets.values():
                self.linker._check(self.owner, target)
                self.linker._on_link(self.owner, target)
                self.linker._link(self.owner, target)

    def exclude(self, *targets):
        """ removes and disconnects targets from the object owning this instance (self.owner) """
        for target in targets:
            if target is not None and target in self.targets.values():
                self.linker._unlink(self.owner, target)
                self.linker._on_unlink(self.owner, target)

    def clear(self):
        """ removes all targets """
        self.exclude(*self.targets.values())

    def one(self):
        """ return a target (e.g. as entry point to the graph """
        for target in self.targets.values():
            return target

    def _set(self, target):
        raise NotImplementedError

    def _del(self, target):
        raise NotImplementedError


class DelegateSet(BaseDelegate, Set):

    def __iter__(self):
        return iter(self.targets.values())

    def __contains__(self, target):
        return id(target) in self.targets

    def __getitem__(self, index):
        """ slow way to getting access to specific targets """
        for i, key in enumerate(self.targets):
            if i == index:
                return self.targets[key]
        raise IndexError(str(index))

    def _set(self, target):
        self.targets[id(target)] = target

    def _del(self, target):
        self.targets.pop(id(target), None)

    def __str__(self):
        return f"{{{', '.join(map(str, self))}}}"

    def __repr__(self):
        return f"{{{', '.join(map(repr, self))}}}"


class DelegateMap(BaseDelegate, Mapping):

    def __init__(self, owner, linker):
        super().__init__(owner, linker)
        self.get_key = linker.get_key

    def __len__(self):
        return len(self.targets)

    def __iter__(self):
        return iter(self.targets)

    def __contains__(self, key):
        return key in self.targets

    def __getitem__(self, key):
        return self.targets[key]

    def rekey(self, old_key_or_target, new_key):
        """ put same target under new _key; maintains order! """
        if isinstance(old_key_or_target, str):
            old_key = old_key_or_target
        else:
            old_key = self.find_key(old_key_or_target)
        keys = list(self.targets)
        index = keys.index(old_key)
        below = {k: self.targets.pop(k) for k in keys[index + 1:]}
        self.targets[new_key] = self.targets.pop(old_key)
        self.targets.update(below)

    def find_key(self, target):
        """ find the key of a target """
        for key, targ in self.targets.items():
            if target is targ:
                return key
        return None

    def _set(self, target):
        self.targets[self.get_key(self.owner, target)] = target

    def _del(self, target):
        for key, targ in self.targets.items():
            if target is targ:
                return self.targets.pop(key, None)

    def __str__(self):
        return str(self.targets)

    def __repr__(self):
        return repr(self.targets)


class BaseLinker(object):
    """
    Baseclass for One and Many descriptors, with shared functionality.
    """
    get_id = id  # default

    _installables = ('iterate', 'visit', 'build', 'gather', 'gather_pairs', 'find', 'reachable', 'walk',
                     'endpoints', 'is_cyclic', 'in_cycle', 'shortest_path', 'save_image')

    def __init__(self, reverse_name=None, cyclic=True, to_self=True, on_link=None, on_unlink=None, install=False, get_id=None):
        """
        :param reverse_name: optional name of the reverse relationship
        :param cyclic: whether the graph is allowed to be cyclic
        :param to_self: whether an node the graph is allowed to connect ot itself
        :param on_link(obj, next_obj): optional callback called just before a connection is made
        :param on_unlink(obj, next_obj): optional callback called just before a connection is broken
        :param get_id(obj): optional alternative callback to uniquely identify nodes
        """
        self.reverse_name = reverse_name
        self.cyclic = cyclic
        self.to_self = to_self
        self._do_on_link = on_link
        self._do_on_unlink = on_unlink
        self._install = install
        self._get_id = get_id or self.get_id
        self.name = None

    @property
    def is_directed(self):
        return self.name != self.reverse_name

    @property
    def installables(self):
        if self._install:
            if isinstance(self._install, (tuple, list)):
                return self._install
            else:
                return self._installables
        return None

    def __set_name__(self, cls, name):
        self.name = name  # sets the name of the attribute when the interpreter first encounters the descriptor in a class
        if self.installables:
            if getattr(cls, '_installed_graph', False):  # there can be only one graph installed
                raise ValueError(f"cannot install graph '{name}', other graph '{cls._installed_graph.name}' already installed")
            cls._installed_graph = self

            # add methods of this class to the class with the graph attribute
            for installable in self.installables:
                installable_func = getattr(self, installable)

                @wraps(installable_func)
                def installed_func(this, *args, __func=installable_func, **kwargs):
                    return __func(this, *args, **kwargs)

                setattr(cls, installable, installed_func)

    def __get__(self, obj, cls=None):
        if obj is None:
            return self  # used to call methods on the descriptor (like 'iterate' below)
        try:
            return obj.__dict__[self.name]
        except KeyError:
            return self._init(obj)  # initializes attribute on first access

    def iterate(self, start_obj, cyclic=False, breadth_first=False):
        """
        iterate through the graph
        :param start_obj: starting object from which the graph is followed
        :param cyclic: whether nodes in the graph will be repeated
        :param breadth_first: depth_first iteration if false (default) else breadth_first iteration
        :yield: nodes in the graph
        """
        yield from Iterator(self.name).iterate(start_obj, cyclic=cyclic, breadth_first=breadth_first)

    __call__ = iterate  # shortcut to iteration

    def visit(self, start_obj, on_visit, cyclic=False, breadth_first=False):
        """ apply 'on_visit(obj, next_obj)' on the graph, other arguments as in 'iterate' """
        visitor = Visitor(self.name)
        return visitor(start_obj, on_visit, cyclic=cyclic, breadth_first=breadth_first)

    def build(self, start_obj, key='__iter__'):
        """
        Build a graph using a key function to find next nodes.
        :param start_obj: entry point object for which the graph is built
        :param key: if str: use attribute with name 'key' of encountered objects to find next objects,
                    if callable: must return the (an iterable of) the next objects in the graph
        :return: self: to chain a call to another method if you like.
        """
        build_on_visit = self._build_on_visit(key, _reg={})
        self.visit(start_obj, on_visit=build_on_visit, breadth_first=True)
        return self

    def gather(self, start_obj):  # bit slow
        """
        Gather all nodes in a graph, going forward and backward if reverse_name is defined.
        """
        get_id = self._get_id

        forw_iterator = Iterator(self.name)
        back_iterator = Iterator(self.reverse_name) if self.reverse_name else None

        gathered = {}
        queue = deque([start_obj])
        while len(queue):
            obj = queue.popleft()
            gathered[get_id(obj)] = obj

            for forw_obj in forw_iterator.iter_object(obj):
                if get_id(forw_obj) not in gathered:
                    queue.append(forw_obj)

            if back_iterator:
                for back_obj in back_iterator.iter_object(obj):
                    if get_id(back_obj) not in gathered:
                        queue.append(back_obj)

        return list(gathered.values())

    def gather_pairs(self, start_obj):  # bit slow
        """
        Gather all connected pairs of nodes in a graph, going forward, and backward if reverse_name is defined.
        """
        get_id = self._get_id

        forw_iterator = Iterator(self.name)
        back_iterator = Iterator(self.reverse_name) if self.reverse_name else None

        gathered = set()
        queue = deque([start_obj])
        pairs = []

        while len(queue):
            obj = queue.popleft()

            for forw_obj in forw_iterator.iter_object(obj):
                key = (get_id(obj), get_id(forw_obj))
                if key not in gathered:
                    pairs.append((obj, forw_obj))
                    queue.append(forw_obj)
                gathered.add(key)

            if back_iterator:
                for back_obj in back_iterator.iter_object(obj):
                    key = (get_id(back_obj), get_id(obj))
                    if key not in gathered:
                        pairs.append((back_obj, obj))
                        queue.append(back_obj)
                    gathered.add(key)
        return pairs

    def find(self, start_obj, filter):
        """ return objects that pass the filer callback """
        return [obj for obj in self.iterate(start_obj, breadth_first=True) if filter(obj)]

    def reachable(self, start_obj, target_obj):
        """ return whether target_obj can be reached from start_obj through the graph """
        iterator = Iterator(self.name)
        for obj in iterator(start_obj):
            if target_obj in iterator.iter_object(obj):
                return True
        return False

    def walk(self, start_obj, key, on_visit=None):
        """
        iterate through the graph, with a key function selecting the next connected node
        :param start_obj: starting point in the graph
        :param key: function to pick the next node in the graph, as in 'next_node = key(node)'
        :param on_visit: optional callback applied to the visited node
        :return: yield nodes encountered in the graph one-by-one
        """
        yield from Iterator(self.name).walk(start_obj, key=key, on_visit=on_visit)

    def endpoints(self, start_obj):
        """ return a list of endpoint nodes (with no next node in the graph), starting from start_obj"""
        endpoints = []
        iterator = Iterator(self.name)
        for obj in iterator(start_obj):
            if not list(iterator.iter_object(obj)):
                endpoints.append(obj)
        return endpoints

    def is_cyclic(self, start_obj):
        """ returns whether any cycles are in the graph reachable from start_obj"""
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
        """ return whether start_obj is in a cycle (whether it can be reached from itself)"""
        return self.reachable(start_obj, start_obj)

    def shortest_path(self, start_obj, target_obj, get_cost=None, heuristic=None):
        """
         Finds the shortest path through the graph from start_obj to target_obj
        :param start_obj: node to start from
        :param target_obj: node to which the path must be calculated
        :param get_cost(node, next_node): cost function: must return cost for following edge between node and next_node. Default
            results in a shortest path defined by the number of edges between start and end.
        :param heuristic(node, target_node): optional heuristic function to calculate an under estimate of the remaining
            cost from a node to the target node (often resulting in faster path_finding, using A*).
        :return: list of nodes of the shortest path
        """
        return Iterator(self.name).shortest_path(start_obj, target_obj,
                                                 get_cost=get_cost,
                                                 heuristic=heuristic)

    def save_image(self, start_obj, filename, label_getter=lambda obj: obj.name,
                   view=False, fontsize='10', fontname='Arial bold', **options):

        if self.is_directed:
            label_pairs = {(label_getter(n1), label_getter(n2))
                           for n1, n2 in self.gather_pairs(start_obj)}
        else:
            label_pairs = {tuple(sorted((label_getter(n1), label_getter(n2))))
                           for n1, n2 in self.gather_pairs(start_obj)}

        save_graph_image(name=self.name,
                         pairs=label_pairs,
                         directed=self.is_directed,
                         view=view,
                         filename=filename,
                         fontsize=fontsize,
                         fontname=fontname,
                         **options)

    def _reverse(self, target):
        if self.reverse_name is None:
            return None
        return getattr(target.__class__, self.reverse_name)

    def _creates_cycle(self, obj, target):
        if obj is target:
            return True
        if self.name == self.reverse_name:
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
        if self.reverse_name:
            self._reverse(target)._set(target, obj)

    def _unlink(self, obj, target=None):
        if target is not None:
            if self.reverse_name:
                self._reverse(target)._del(target, obj)
            self._del(obj, target)

    def _on_link(self, obj, target, _remote=False):
        if self._do_on_link:
            return self._do_on_link(obj, target)
        if self.reverse_name and not _remote:
            return self._reverse(target)._on_link(target, obj, True)

    def _on_unlink(self, obj, target, _remote=False):
        if self._do_on_unlink:
            return self._do_on_unlink(obj, target)
        if self.reverse_name and not _remote:
            return self._reverse(target)._on_unlink(target, obj, True)

    def _init(self, obj):
        raise NotImplementedError

    def _set(self, obj, target):
        raise NotImplementedError

    def _del(self, obj, target):
        raise NotImplementedError

    def _existing(self, obj, target):
        raise NotImplementedError

    def _build_on_visit(self, key, _reg):
        raise NotImplementedError


class One(BaseLinker):

    def __set__(self, obj, target):
        self._check(obj, target)
        self._unlink(obj)
        if target is not None:
            if self.reverse_name:
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
            if isinstance(key, str):
                target = getattr(obj, key)
            else:
                target = key(obj)
            id_ = get_id(target)
            if id_ in _reg:  # already added to graph
                target = _reg[id_]
            else:
                _reg[id_] = target
            setattr(obj, self.name, target)

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
        self.__get__(obj).clear()
        self.__get__(obj).include(*targets)

    def __delete__(self, obj):
        self.__get__(obj).clear()

    def _build_on_visit(self, key, _reg):
        name = self.name
        get_id = self._get_id

        def visit(obj, key=key):
            if isinstance(key, str):
                key = getattr(obj.__class__, key)
            for target in key(obj):
                id_ = get_id(target)
                if id_ in _reg:
                    target = _reg[id_]
                else:
                    _reg[id_] = target
                getattr(obj, name).include(target)

        return visit

    def _init(self, obj):
        obj.__dict__[self.name] = self.many_class(obj, linker=self)
        return obj.__dict__[self.name]

    def _set(self, obj, target):
        self.__get__(obj)._set(target)

    def _del(self, obj, target):
        self.__get__(obj)._del(target)


class Many(BaseMany):
    many_class = DelegateSet

    def _existing(self, obj, target):
        return target in self.__get__(obj)


class ManyMap(BaseMany):
    many_class = DelegateMap

    def __init__(self, *args, key_attr='name', **kwargs):
        super().__init__(*args, **kwargs)
        self.key_attr = key_attr

    def get_key(self, obj, target):
        return unique_name(self.__get__(obj),
                           target.__class__.__name__.lower(),
                           getattr(target, self.key_attr, None))

    def _existing(self, obj, target):
        return target in self.__get__(obj).values()


if __name__ == '__main__':
    pass
