from anygraph import One
from anygraph.linkers import BaseMany


class GraphicsOptions(object):
    shapes = {'rectangle', 'ellipse'}
    directions = {'vertical', 'horizontal', 'circular'}

    default_width = 1
    default_height = 1

    def __init__(self, get_text, get_width, get_height=None, get_shape='ellipse', direction='circular'):
        self._get_text = get_text
        self._get_width = get_width
        self._get_height = get_height or get_width
        if get_shape not in self.shapes:
            raise ValueError(f"parameter 'shape' is '{get_shape}'; it must be in [{self.shapes}]")
        self._get_shape = get_shape
        if direction not in self.directions:
            raise ValueError(f"parameter 'direction' is '{direction}'; it must be in [{self.directions}]")
        self.direction = direction

    def _get_attr(self, node, key, default):
        if isinstance(key, str):
            return getattr(node, key, default)
        return key(node)

    def get_text(self, node):
        return self._get_attr(node, self._get_text, default=type(node).__name__.lower())

    def get_width(self, node):
        return self._get_attr(node, self._get_width, default=self.default_width)

    def get_height(self, node):
        return self._get_attr(node, self._get_width, default=self.default_height)

    def get_shape(self, node):
        return self._get_attr(node, self._get_shape, default='ellipse')



class GraphPlotter(object):

    def __init__(self, graphics_options):
        self.graphics_options = graphics_options

    def analyse(self, node, name):
        if isinstance(getattr(type(node), name), One):
            pass
        elif isinstance(getattr(type(node), name), BaseMany):
            pass
        else:
            raise TypeError(f"cannot analyse: invalid attribute {name} in {type(node).__name__}")

    def get_nodes(self, node, name):
        return getattr(type(node), name).gather(node)

    def sort(self, node, name):
        nodes = self.get_nodes(node, name)





