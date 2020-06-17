import unittest
from itertools import product

from anygraph import Many, One, Iterator, GetEndpoints
from anygraph.tools import chained, flipcoin


class TestPropagator(unittest.TestCase):
    class TestMany(object):
        nexts = Many('prevs')
        prevs = Many('nexts')

        def __init__(self, name):
            self.name = name

    def create_objects(self, count=10):
        objs = [self.TestMany('bob_' + str(i)) for i in range(count)]
        for i, obj in enumerate(objs):
            for next_obj in objs[i + 1:]:
                obj.nexts.include(next_obj)
        return objs

    def back_wire(self, objs):
        for obj1 in objs:
            for obj2 in objs:
                if obj2 in obj1.nexts:
                    obj2.nexts.add(obj1)

    def test_iterate(self):
        count = 10
        objs = self.create_objects(count)
        for breadth_first in [False, True]:
            iterator = Iterator('nexts')
            assert len(list(iterator.iterate(objs[0], breadth_first=breadth_first))) == count

            iterator = Iterator('prevs')
            assert len(list(iterator.iterate(objs[count - 1], breadth_first=breadth_first))) == count

    def test_endpoint(self):
        class StartPoint(object):
            next = One('prev')

        class EndPoint(object):
            prev = One('next')

        start = StartPoint()
        endpt = EndPoint()
        start.next = endpt

        get_endpoints = GetEndpoints('next')
        assert get_endpoints(start) == [endpt]


class testPathMethods(unittest.TestCase):

    """ lets find a path between 2 nodes (not lowest, might use astar; left as exercise to the reader ;-) """

    def test_dijkstra(self):
        class Node(object):
            """ bidirectional graph nodes connected via 'nexts' and in reverse via 'prevs' """
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, num):
                self.num = num

            def __str__(self):
                return f"Node({self.num})"

        def create_nodes(count):
            return [Node(i) for i in range(count)]

        def create_matrix(size, prob=0.5):
            matrix = []
            for i in range(size):
                matrix.append([flipcoin(prob) for _ in range(size)])
            for i in range(size - 1):  # to take care that there is always a path
                matrix[i][i + 1] = True
            return matrix

        def connect_nodes(nodes, matrix):
            assert len(nodes) == len(matrix)
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if matrix[i][j]:
                        node1.nexts.include(node2)

        size, prob = 10, 0.2
        matrix = create_matrix(size, prob=prob)
        nodes = create_nodes(size)
        connect_nodes(nodes, matrix)

        path = Node.nexts.shortest_path(nodes[0], nodes[-1])
        if path:  # occasionally there is no path due to random matrix
            for o1, o2 in chained(path):
                assert o2 in o1.nexts

    def test_astar(self):

        class Node(object):
            """ bidirectional graph nodes connected via 'nexts' and in reverse via 'prevs' """
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, i, j):
                self.index = (i, j)

            def __str__(self):
                return f"Node({self.index[0]}, {self.index[1]})"

        def create_nodes(count):
            nodes = []
            for i in range(count):
                for j in range(count):
                    nodes.append(Node(i, j))
            return nodes

        def connect_nodes(nodes):
            nodes_dict = {n.index: n for n in nodes}
            for (i, j), node in nodes_dict.items():
                for di, dj in product([-1, 0, 1], [-1, 0, 1]):
                    try:
                        if flipcoin() or i == 0 or j == 0:
                            node.nexts.include(nodes_dict[i + di, j + dj])
                    except KeyError:
                        pass

        size = 10
        nodes = create_nodes(size)
        connect_nodes(nodes)

        def weight(node1, node2):
            i1, j1 = node1.index
            i2, j2 = node2.index
            return abs(i1 - i2) + abs(j1 - j2)

        path = Node.nexts.shortest_path(nodes[0], nodes[-1], get_cost=weight, heuristic=weight)
        if path:  # occasionally there is no path due to random matrix
            for o1, o2 in chained(path):
                assert o2 in o1.nexts
