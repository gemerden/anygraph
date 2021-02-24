"""
Here we will show how to build a graph from a class inheritance structure. Since we will n change the class of classes (type), we will use a wrapper to do this.
"""
from anygraph import Many

""" 
First we define the wrapper class; because we create instances of ClassWrapper on the flight; 
to detect if the class was already encountered, we need to use a custom get_id function.
"""

class ClassWrapper(object):
    """ add the graph definition to the wrapper class """
    base_classes = Many('sub_classes', cyclic=False, get_id=lambda w: id(w.wrapped))  # the id() of the classes themselves
    sub_classes = Many('base_classes', get_id=lambda w: id(w.wrapped))

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        """ simple way to access the wrapped class """
        return getattr(self.wrapped, name)


""" then we define how to get from a wrapped class to its base classes"""
def get_bases(wrapper):
    """ pre-wraps the classes to be able to use 'base_classes' and 'sub_classes' """
    for cls in wrapper.wrapped.__bases__:
        yield ClassWrapper(cls)


""" and we are ready to build the graph """
def build(cls):
    wrapped_class = ClassWrapper(cls)
    ClassWrapper.base_classes.build(wrapped_class, key=get_bases)
    return wrapped_class


if __name__ == '__main__':
    """ create some class hierarchy: """

    class A(object): pass
    class B(A): pass
    class C(A): pass
    class D(B, C): pass
    class E(D): pass

    start = build(E)

    """ let's see what we got """
    print([w.__name__ for w in ClassWrapper.base_classes(start, breadth_first=True)])

    """ find the wrapper wrapping the object class """
    wrapped_object = ClassWrapper.base_classes.find(start, filter=lambda w: w.wrapped is object)[0]

    """ and following the 'sub_classes' reverse graph """
    print([w.__name__ for w in ClassWrapper.sub_classes(wrapped_object, breadth_first=True)])

    """
    Note that iterating over base_classes depth- or breadth-first, does not 
    always produce the same order as the mro() algorithm used by python 
    """




