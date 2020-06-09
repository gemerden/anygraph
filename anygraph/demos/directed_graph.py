from anygraph import Many


class Node(object):
    nexts = Many('prevs')
    prevs = Many('nexts')


if __name__ == '__main__':
    node_1 = Node()
    node_2 = Node()
    node_3 = Node()

    node_1.nexts = [node_2, node_3]
    node_2.nexts.add(node_3)
    node_3.nexts.add(node_1)

    assert set(node_3.prevs) == {node_1, node_2}
