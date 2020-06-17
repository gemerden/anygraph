from anygraph import Many
from anygraph.tools import flipcoin, stopwatch


class Node(object):
    """ bidirectional graph nodes connected via 'adjacent' """
    adjacent = Many('adjacent')

    def __init__(self, i, j):
        self.index = (i, j)

    def __str__(self):
        return f"Node({self.index[0]}, {self.index[1]})"


def create_nodes_dict(side):
    """ create nodes in a grid """
    nodes = {}
    for i in range(side):
        for j in range(side):
            nodes[i, j] = Node(i, j)
    return nodes


def connect_nodes(nodes_dict, prob=0.5):
    """ connect nodes with neighbours """
    for (i, j), node in nodes_dict.items():
        for di, dj in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if flipcoin(prob):
                try:
                    node.adjacent.include(nodes_dict[i + di, j + dj])
                except KeyError:  # index outside grid
                    pass

    """ make certain there is at least one path (random adjacents might cause that no path is present)"""
    side = max(nodes_dict)[0] + 1  # quick and dirty retrieve grid side size
    for i in range(side - 1):
        nodes_dict[i, i].adjacent.include(nodes_dict[i, i + 1])
        nodes_dict[i, i + 1].adjacent.include(nodes_dict[i + 1, i + 1])


""" lets run: create nodes and connect """
size = 25
nodes_dict = create_nodes_dict(size)
connect_nodes(nodes_dict)


""" using the sum metric (manhattan distance) based on location in the grid as weights for edges """
def manhattan_distance(node1, node2):
    i1, j1 = node1.index
    i2, j2 = node2.index
    return abs(i1 - i2) + abs(j1 - j2)


""" lets pick a start and end node for the path in opposite corners"""
start_node, end_node = nodes_dict[0, 0], nodes_dict[size - 1, size - 1]

""" when no heuristic function is available (an under-estimate from any node to the endpoint) dijkstra is used """
path = Node.adjacent.shortest_path(start_node, end_node,
                                   get_cost=manhattan_distance)
print('path (dijkstra) =', [p.index for p in path], 'length = ', len(path))

""" otherwise astar (faster) is used. note that the heuristic function calculates the sum distance for non-connected nodes """
path2 = Node.adjacent.shortest_path(start_node, end_node,
                                    get_cost=manhattan_distance,
                                    heuristic=manhattan_distance)
print('path (astar)    =', [p.index for p in path2], 'length = ', len(path2))
