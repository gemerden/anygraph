"""
Here we will create a tree graph, using inheritance have separate classes for the tree root/stem and leaves.

"""
from anygraph import Many, One


class ParentNode(object):
    children = Many('parent')


class ChildNode(object):
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
"""


class ParentNode(object):
    parent = None
    children = Many('parent')

    def iterdown(self):
        """
        Iterate through the tree 'under' self; use self.__class__ to access the methods('iterate') of the Many descriptor
        """
        yield from self.__class__.children.iterate(self)


class ChildNode(object):
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
