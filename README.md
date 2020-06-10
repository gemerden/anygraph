# Anygraph

_The easiest way to construct and use most type of graphs_

## Introduction
Anygraph is a very easy to use library to add double sided relationships between objects. This can be used to construct trees, directed and non-directed graphs and chains of objects.

Anygraph also includes some methods like depth and breadth-first iteration as well as Dijkstra and Astar shortest path algorithms.

##Installation
Anygraph can be installed using pip:

`pip install anygraph`

##Samples
Many examples can be found in the 'demos' and 'recipes' directories. Below are some of the basics:

These definitions are sufficient to create different graphs:
````
from anygraph import One, Many

# a non-directed graph
class Person(object):
    friends = Many('friends') 

# a directed graph with reverse edges
class Node(object):
    nexts = Many('prevs')
    prevs = Many('nexts')

# a tree graph
class TreeNode(object):
    parent = One('children')
    children = Many('parent')

# or a chain of objects
class Link(object):
    next_link = One('prev_link')
    prev_link = One('next_link')
     
````
This also means that you can easily add a graph structure to existing objects, just by adding a definition as seen above.

The next step is to actually construct a graph; linking the nodes together. Let's take the tree graph as an example, since it uses both `One` and `Many`:
````
node_1 = TreeNode()
node_2 = TreeNode()
node_3 = TreeNode()
node_4 = TreeNode()

# lets give node_1 some children
node_1.children = [node_2, node3]

# check whether node_2 and node_3 have the right parent
assert node_2.parent is node_1
assert node_3.parent is node_1

# let node_4 be a child of node_1 too
node_4.parent = node_1  # does exactly the same as 'node_1.children.add(node_4)' 
assert node_4 in node_1.children

# we can mode node_4 to be a child of node_2
node_2.children.add(node_4)
assert node_4.parent is node_2
assert node_4 not in node_1.children

````
In short: operations on a `One` or `Many` relationship will always **update the reverse relationships** and break existing when needed.

A `One` relationship supports the normal attribute operations: `n.parent = child`, `del n.parent`, `n.parent = None` (same as `del`)

A `Many` relationship supports the same methods and operations as abc.MutableSet (`.add`, `.remove`, `.disard`, `.update` + `&`, `|` `-`, etc.)  


 
