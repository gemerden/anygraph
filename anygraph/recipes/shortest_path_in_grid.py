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
                    node.adjacent.add(nodes_dict[i + di, j + dj])
                except KeyError:  # index outside grid
                    pass

    """ lets put in a few blocking walls to make the path finding more interesting (and show the advantage of astar)"""
    side = max(nodes_dict)[0] + 1  # quick and dirty retrieve grid side size

    for i in range(0, side // 2 - 1):
        del nodes_dict[side // 2, i].adjacent
        del nodes_dict[i, side // 2].adjacent

    """ make certain there is at least one path (random adjacents might cause that no path is present)"""
    for i in range(side-1):
        nodes_dict[i, i].adjacent.add(nodes_dict[i, i + 1])
        nodes_dict[i, i + 1].adjacent.add(nodes_dict[i + 1, i + 1])


def print_grid(nodes_dict, path=None):
    nd = nodes_dict
    side = max(nd)[0]

    def print_header_line():
        print(' ', end='')
        for i in range(side + 1):
            print(f"{i:3}", end=' ')
        print()

    def print_node_link_line(row):
        print(f"{row:2}", end=' ')
        for j in range(side):
            if path and nd[row, j] in path:
                if nd[row, j + 1] in path:
                    print('X', end=' \u2550 ')
                else:
                    print('X', end='   ')
            elif nd[row, j] in nd[row, j + 1].adjacent:
                print('O', end=' \u2015 ')
            elif not len(nd[row, j].adjacent):
                print(' ', end='   ')
            else:
                print('O', end='   ')
        if path and nd[row, size - 1] in path:
            print('X')
        elif not len(nd[row, size - 1].adjacent):
            print(' ')
        else:
            print('O')

    def print_vert_link_line(row):
        print('  ', end=' ')
        for j in range(side+1):
            if path and nd[row, j] in path and nd[row + 1, j] in path:
                print('\u01C1', end='   ')
            elif nd[row, j] in nd[row + 1, j].adjacent:
                print('|', end='   ')
            else:
                print(' ', end='   ')
        print()

    print_header_line()
    for i in range(side):
        print_node_link_line(i)
        print_vert_link_line(i)
    print_node_link_line(side)
    print('\n')


""" lets run: create nodes and connect """
size = 25
prob = 0.4
nodes_dict = create_nodes_dict(size)
connect_nodes(nodes_dict, prob)

""" using the sum metric (manhattan distance) based on location in the grid as weights for edges """
def manhattan_distance(node1, node2):
    i1, j1 = node1.index
    i2, j2 = node2.index
    return abs(i1 - i2) + abs(j1 - j2)


""" lets pick a start and end node for the path in opposite corners"""
start_node, end_node = nodes_dict[0, 0], nodes_dict[size - 1, size - 1]

""" when no heuristic function is available (an under-estimate from any node to the endpoint) dijkstra is used """
path1 = Node.adjacent.shortest_path(start_node, end_node,
                                    get_cost=manhattan_distance)
print('path (dijkstra) =', [p.index for p in path1], 'length = ', len(path1))

""" otherwise astar (faster) is used. note that the heuristic function calculates the sum distance for non-connected nodes """
path2 = Node.adjacent.shortest_path(start_node, end_node,
                                    get_cost=manhattan_distance,
                                    heuristic=manhattan_distance)
print('path (astar)    =', [p.index for p in path2], 'length = ', len(path2))

""" these paths will (should ;-) always have the same length (astar is just faster in case direct routes are blocked)! """
print(f"\ndijkstra found a path of length {len(path1)}; astar found a path of length {len(path2)}\n")

""" just for fun, let's compare the speeds """

repeat = 1000

with stopwatch() as watch:
    for _ in range(repeat):
        path = Node.adjacent.shortest_path(start_node, end_node,
                                           get_cost=manhattan_distance)

print(f"{repeat} dijkstra took {round(watch(), 4)} seconds")

with stopwatch() as watch:
    for _ in range(repeat):
        path = Node.adjacent.shortest_path(start_node, end_node,
                                           get_cost=manhattan_distance,
                                           heuristic=manhattan_distance)

print(f"{repeat} astar    took {round(watch(), 4)} seconds\n")

""" and show the paths in the grid """
print('dijkstra:\n')
print_grid(nodes_dict, path1)

print('astar:\n')
print_grid(nodes_dict, path2)
