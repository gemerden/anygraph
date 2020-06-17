from anygraph import Many, One

""" create a graph from a matrix of weights indicating whether two nodes are connected """


class Node(object):
    """ bidirectional graph nodes connected via 'nexts' and in reverse via 'prevs' """
    nexts = Many('prevs')
    prevs = Many('nexts')

    def __init__(self, num):
        self.num = num

    def __str__(self):
        return f"Node({self.num})"


if __name__ == '__main__':
    import random

    def flip_coin(prob=0.5):
        return random.random() < prob

    def create_matrix(size):
        """ create a matrix with reandom booleans indicating whether the corresponding nodes must be connected """
        matrix = []
        for i in range(size):
            matrix.append([flip_coin() for _ in range(size)])
        return matrix

    def create_nodes(count):
        """ create some unconnected nodes """
        return [Node(i) for i in range(count)]

    def connect_nodes(nodes, matrix):
        """ this is the function that actually wires the nodes together using the matrix """
        assert len(nodes) == len(matrix)
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if matrix[i][j]:
                    node1.nexts.include(node2)

    """ lets make and print the connections in matrix form (c = connected) """

    size = 10
    matrix = create_matrix(size)
    nodes = create_nodes(size)
    connect_nodes(nodes, matrix)

    def print_matrix(matrix):
        print(' ', end=' ')
        for i in range(size):
            print(i, end=' ')
        print()
        for j, row in enumerate(matrix):
            print(j, end=' ')
            for cell in row:
                if cell:
                    print('c', end=' ')
                else:
                    print(' ', end=' ')
            print()

    print_matrix(matrix)

    """ and check whether the reversed connections are there """

    def check_reverse(nodes, matrix):
        assert len(nodes) == len(matrix)
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if matrix[i][j]:
                    assert node1 in node2.prevs
                else:
                    assert node1 not in node2.prevs


