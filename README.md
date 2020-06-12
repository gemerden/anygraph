# Anygraph

_The easiest way to construct and use graphs in Python_

## Introduction

Graphs and especially double-linked graphs (with relations going for- and backwards) are often useful, but easy to get wrong. After having written a number of tree and other graph libraries, usually as mixin classes, I found a different solution that has a number of advantages. Is consists of only 2 classes: `One` and `Many` and only a few optional parameters. With these classes you can create many types of graph, which in turn opens the way to a number of (included) algorithms associated with graphs and graph traversal.    

_Anygraph_ is a very easy-to-use library to add single and double sided relationships between objects. This can be used to construct trees, directed and non-directed graphs, cyclic and non-cyclic graphs.

_Anygraph_ also includes methods for:
* single- and double-linked graphs
* Depth and breadth-first iteration,
* Building a graph from any relationship between objects, of the same or different classes,
* Dijkstra and A* shortest path algorithms,
* Applying a function to each connected node in the graph, possibly altering the graph, 
* Traversing the graph with a key-function to select the next node,
* Checking for cycles or if a node is reachable from another node,

No inheritance is needed, a graph structure can simply be added to a class by setting one or two class attributes on your (possibly existing) class.

## Installation

Anygraph can be installed using pip:

`> pip install anygraph`

Anygraph has _no dependencies_.

## Testing

Unittests can be found in `anygraph/unittests`

## Samples

More examples can be found in the `demos` and `recipes` directories. Below are some of the basics:

### The Basics

Anygraph uses two classes: `One` and `Many`. Single linked graphs enable a number of algorithms (as long as ou follow the graph only in one direction) and can be defined as follows:
```python
from anygraph import One, Many

class SomeLink(object): # a directed chain
    next_link = One()

class SomeNode(object): # a directed graph
    next_nodes = Many() 
```
More powerful is the ability to create double linked graphs. In that case only giving the name of the reverse relationship is sufficient:
```python
class Person(object): # a non-directed graph
    friends = Many('friends') 

class Node(object): # a directed graph with reverse relationship
    nexts = Many('prevs')
    prevs = Many('nexts')

class TreeNode(object):  # a tree graph
    parent = One('children')
    children = Many('parent')

class Link(object): # or a chain of objects
    next_link = One('prev_link')
    prev_link = One('next_link')
```
This also means that you can easily add a graph structure to existing objects, just by adding a class attribute. Note that any names can be used, names like 'parent' are used for clarity.

The next step is to actually construct a graph; linking the nodes together. Let's take the tree graph as an example, since it uses both `One` and `Many`, double-linked:
```python
nodes = [TreeNode() for _ in range(4)]

# lets give nodes[0] some children
nodes[0].children = [nodes[1], nodes[2]]  # or nodes[0].update([nodes[1], nodes[2]])

# check whether nodes[1] and nodes[2] have the right parent
assert nodes[1].parent is nodes[0]
assert nodes[2].parent is nodes[0]

# let nodes[3] be a child of nodes[0] too
nodes[3].parent = nodes[0]  # or 'nodes[0].children.add(nodes[3])' 
assert nodes[3] in nodes[0].children

# let nodes[3] be a child of nodes[1]
nodes[1].children.add(nodes[3])
assert nodes[3].parent is nodes[1]
assert nodes[3] not in nodes[0].children
```
In short: changes to a `One` or `Many` relationship will always **update the reverse relationships** and break existing relationships when needed.

* A `One` relationship supports the normal attribute operations: `n.parent = child`, `del n.parent`, `n.parent = None` (same as `del`)
* A `Many` relationship supports the same methods and operations as abc.MutableSet (`.add`, `.remove`, `.discard`, `.update` + `&`, `|` `-`, etc.)  

Note that the insertion order of the children is maintained; the underlying data-structure is a `dict`, not a `set`. Any object can be used as node in the graph, not only objects that are hashable. 

### Cycles in Graphs

If you do not want to have cycles in the graph, you can set (for example):
```python
class Node(object):
    nexts = Many(cyclic=False)

node1, node2 = Node(), Node()
node1.nexts.add(node2)
node2.nexts.add(node1)  # raises ValueError
```
When you create a link that would create a cycle in the graph, this will raise a `ValueError`. This will also prevent a cycle to be created through the reverse `prevs` relationship. Note that a non-directed graph is always cyclic (I am a friend of my friend).

To check whether a node is in a cycle, call `Node.nexts.in_cycle(some_node)`. To check whether there are any cycles in the graph reachable from a node, call `Node.nexts.is_cyclic(some_node)`. These can only be the case if `cyclic=True`: the default.

### Self-reference

If you want to prevent objects from having a relationship to themselves, use:
```python
class Node(object):
    nexts = Many(to_self=False)

node = Node()
node.nexts.add(node)  # raises ValueError
```
This will also cause a `ValueError` to be raised when tried. Note that `cyclic=False` will also prevent self-reference.

### Graph Iteration

There are several ways to iterate through a graph. Most common are depth first and breadth first. Both are supported out of the box. For example:
```python
class Person(object):
    friends = Many('friends') 

bob = Person()
ann = Person()
ann.friends.add(bob)
# ... create a network of friends

# iterate through the graph in depth first order
for friend in Person.friends.iterate(bob):  # note we call friends on Person, not bob
    print(friend)

# or short
for friend in Person.friends(bob): 
    print(friend)
```
This will iterate through the graph, by default not in cycles and depth-first. To change this do (for example):
```python
for friend in Person.friends(bob, cyclic=True, breadth_first=True):
    print(friend)
```
If nodes are not reachable from the starting node through the graph, they will not show up during iteration. If you wan to check reachability, do `Person.friends.reachable(from_person, to_person)`, in the example above.

### Building a Graph

Graphs can often be automatically constructed by using the 'build' method. This only needs a function or method_name (or attribute name for `One` relationships). An rudimentary example:
```python
from anygraph import One, Many

class Items(object):
    children = Many('parent')

    def __init__(self, items=None):
        self.items = items or []

    def extend(self, items):
        self.items.extend(items)

    def __iter__(self):
        return iter(self.items)

class Item(object):
    parent = One('children')

    def siblings(self):  # only works after the graph has been built
        return [s for s in self.parent.children if s is not self] 

# add items to an Items object
items = [Item() for _ in range(5)] 
items_obj = Items(items)

assert items[0].parent is None  # nothing yet

Items.children.build(items_obj)  # build the graph! give an entry point object to build the graph from

# which is the same as
Items.children.build(items_obj, key='__iter__')  # '__iter__' is the default

# or
Items.children.build(items_obj, key=lambda obj: obj.items)

# and now
assert all(item.parent is items_obj for item in items_obj)
assert items[0].siblings() == items[1:]
```
This makes all objects iteratively encountered by `build()` be part of the graph, to be iterated (depth- or breadth-first), traversed upward and downward; it makes the `Item.siblings()` method work. As long as a iterable relationship between objects exists or can be created, a double-linked graph can be built automatically.

Notes:
* The `key` function must return an iterable, this can also be a generator,
* The graph can traverse multiple unrelated object types/classes, as long as they have One or Many relationships defined with the same name,
* The graph will build cyclic relationships when it encounters repeated instances, identified with the python `id` function. This can be overridden by setting another id function in the relationship constructor, as in: `children = Many('parent', get_id=lambda obj: obj.name)`. 

A more in-depth example can be found in `anygraph\recipes\building_a_graph.py`
### Visiting the Graph

Another useful utility is the `.visit()` method. It is used to traverse the graph and apply a function/callable on any node encountered (using the example above):
```python
objs = []
def visit(obj):
    objs.append(obj)

Items.children.visit(items_obj, on_visit=visit)

assert objs == [items_obj] + items
```
Again the iteration order and allowing cycles in the iteration can be modified with `breadth_first` and `cyclic` (see Iteration).

### Shortest Path

Often a shortest path between to nodes in a graph must be found (e.g. in route-planners or in games). _Anygraph_ provides two algorithms to calculate shortest path.Let's say we have a graph consisting of nodes that have already been connected and we want the shortest route between the first and last node (or between any other nodes):
```python
class Node(object):
    nexts = Many('prevs')
    prevs = Many('nexts')

nodes = create_and_connect_nodes()

# we need a cost function to be able to define shortest. The function below minimizes the number of edges in the path.
def cost(node1, node2):
    if node1 is node2:
        return 0
    return 1

# shortest path
path = Node.nexts.shortest_path(nodes[0], nodes[-1], get_cost=cost)

# If a (lower-) estimate of the remaining cost from any node to the target node can be made:
def heuristic(node1, node2):
    return 'lower estimate of cost from node1 to node2'

#shortest path but faster
path = Node.nexts.shortest_path(nodes[0], nodes[-1], get_cost=cost, heuristic=heuristic)
```
With a heuristic function, the A* algorithm is used; without, the method falls back to Dijkstra. A lower estimate means that the estimate is always smaller or equal than the real cost. In geographic pathfinding the heuristic is often the distance or traveltime to the endpoint without obstructions. 

A more in-depth example can be found in `anygraph\recipes\shortest_path_in_grid.py`

### Walking the Graph

Another option is to iterate through the graph by picking the next node with a key function:
```python
class Person(object):
    friends = Many('friends')

people = create_and_connect_people()

# as an example, a random walk through the graph can be created with:
for person in Person.friends.walk(people[0], key=lambda p: random.random()):
    print(person)

# if you want a node to be pre-processed before showing up in the iteration, you can pass an on_visit function
for person in Person.friends.walk(people[0], key=lambda p: random.random(), on_visit=lambda p: print(p)):
    pass

```
`walk()` will run forever unless a dead-end is encountered (in the non-directed graph above this will never happen, because the the walk can always return to the last node) or you `break` out of the loop. Picking the next node essentially happens through `next_node = min(next_nodes, key=key)`. 

### Mixed Nodes

The nodes in the graph do not have to be of the same class, as long as the relationships have the same name. Let's give edges in the graph their own class:
```python
from anygraph import One, Many

class Node(object):
    nexts = Many('prevs')
    prevs = Many('nexts')

class Edge(object):  # an edge only connects to one node on each end
    nexts = One('prevs')
    prevs = One('nexts')

    def __init__(self, prev, next):
        self.prevs = prev
        self.nexts = next

def create_and_connect_nodes(num):
    """ for example: connect all nodes with all nodes """
    nodes = [Node() for _ in range(num)]
    for node1 in nodes:
        for node2 in nodes:
            Edge(node1, node2)
    return nodes

nodes = create_and_connect_nodes(5)

# now lets run through the graph.
for node_or_edge in Node.nexts(nodes[0]):  # or Node.prevs(nodes[0]) to follow the reverse graph
    print(node_or_edge.__class__.__name__)

"""
This will print:
Node
Edge
Node
Edge
etc. 
"""
```

### Callbacks

The `One` and `Many` classes support 2 callbacks: `on_link(obj, linked_obj)` and `on_unlink(obj, linked_obj)`. For example in the mixed node example above, you might want to prevent dangling Edge objects (only linked on one side). This can be achieved by using `on_unlink`, as in:
```python
def on_next_unlink(obj, linked_obj):
    del obj.prevs
    
def on_prev_unlink(obj, linked_obj):
    del obj.nexts
    
class Edge(object):  # an edge only connects to one node on each end
    nexts = One('prevs', on_unlink=on_next_unlink)
    prevs = One('nexts', on_unlink=on_prev_unlink)
```

## Authors

Contributing authors are:

* Lars van Gemerden - initial work - _rational-it_

## License

This project is licensed under the MIT License - see the `LICENSE.txt` file for details

