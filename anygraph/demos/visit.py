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

    visited = []
    def on_visit(obj):
        visited.append(obj)

    Node.nexts.visit(node_1, on_visit=on_visit)  # start in node_1

    assert visited == [node_1, node_2, node_3]

    visited = []
    def on_visit(obj):
        if len(visited) >= 6:
            raise StopIteration
        visited.append(obj)


    # with 'cyclic=True' nodes can be visited multiple times if graph is cyclic
    Node.nexts.visit(node_1, on_visit=on_visit, cyclic=True)

    assert visited == [node_1, node_2, node_3, node_1, node_2, node_3]

    # graph can also be iterated over in 'breadth_first' order
    del visited[:]
    Node.nexts.visit(node_1, on_visit=on_visit, cyclic=True, breadth_first=True)

    assert visited == [node_1, node_2, node_3, node_3, node_1, node_1]






