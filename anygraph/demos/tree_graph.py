from anygraph import Many, One


class Node(object):
    parent = One('children')
    children = Many('parent')


if __name__ == '__main__':
    node_1 = Node()
    node_2 = Node()
    node_3 = Node()
    node_4 = Node()

    node_1.children = [node_2, node_3]
    node_2.children.include(node_4)
    node_4.parent = node_3  # no longer child of node_2

    assert node_1.children == {node_2, node_3}
    assert node_2.parent is node_1
    assert node_2.children == set()
    assert node_3.children == {node_4}

    node_1.children.clear()

    assert node_1.children == set()
    assert node_2.parent is None
