import random
from contextlib import contextmanager
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


def save_graph_image(name, pairs, directed=True, filename='png', view=True, **options):
    try:
        import graphviz
    except Exception as error:
        raise RuntimeError(f"graphviz cannot be imported to save graph image: {error}")

    file_parts = filename.rsplit('.', 1)
    if len(file_parts) == 1:  # just an extension
        filename = name
    else:
        filename = file_parts[0]

    if directed:
        dot = graphviz.Digraph(comment=name,
                               format=file_parts[-1],
                               node_attr=options)
    else:
        dot = graphviz.Graph(comment=name,
                             format=file_parts[-1],
                             node_attr=options)

    for label1, label2 in pairs:
        dot.edge(label1, label2)

    dot.render(filename, view=view)
    return dot
