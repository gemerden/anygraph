"""
Here we will create a tree graph, using inheritance have separate classes for the tree root/stem and leaves.

"""
from anygraph import Many, One

class BaseNode(object):
    """ just add a name for printing """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class ParentNode(BaseNode):
    children = Many('parent')


class ChildNode(BaseNode):
    parent = One('children')


class TreeRoot(ParentNode):
    """ cannot have a parent, so does not inherit from ChildNode"""
    pass


class TreeBranch(ChildNode, ParentNode):
    """ can have both parent and children """
    pass


class TreeLeaf(ChildNode):
    """ does not have children (think files in a file system) """
    pass

"""
That is basically all, but not that interesting yet. Using the relationships you can easily add useful methods to the classes.

We will re-use the names for readability. 
"""


class ParentNode(BaseNode):
    parent = None
    children = Many('parent')

    def iterdown(self):
        """
        Iterate through the tree 'under' self; use self.__class__ to access the methods('iterate') of the Many descriptor
        """
        yield from self.__class__.children.iterate(self)


class ChildNode(BaseNode):
    parent = One('children')

    def root(self):
        return self.parent.root()

    def siblings(self):
        """ siblings are the other children of the parent """
        return [child for child in self.parent.children if child is not self]

    def iterup(self):
        """ iterate up through the tree """
        parent = self
        while parent:
            yield parent
            parent = parent.parent


class TreeRoot(ParentNode):

    def root(self):
        """ override .root() to not look in a (absent) parent """
        return self


class TreeBranch(ChildNode, ParentNode):
    pass


class TreeLeaf(ChildNode):
    pass


""" 
Note that the methods of Many/One are useful but often not needed. The calling pattern to use the methods in One/Many 
can be seen in ParentNode.iterdown().

"""


""" let's try it out """
if __name__ == '__main__':

    root = TreeRoot('root')
    root.children = [TreeBranch(f"branch_{i}") for i in range(3)]
    for i, branch in enumerate(root.children):
        branch.children = [TreeLeaf(f"leaf_{i}_{j}") for j in range(2)]

    """ get the TreeLeaf nodes """
    leaves = list(ParentNode.children.endpoints(root))

    print('all the leaves:', leaves)

    """ check the root """
    assert all(leaf.root() is root for leaf in leaves)

    """ check siblings """
    a_branch = list(root.children)[0]
    assert a_branch.siblings() == list(root.children)[1:]




