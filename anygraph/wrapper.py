class Wrapper(object):
    wrapper_classes = {}

    @classmethod
    def wrap(cls, obj):
        return cls(obj)

    def __init__(self, wrapped):
        self.__dict__['wrapped'] = wrapped

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def __setattr__(self, name, value):
        setattr(self.wrapped, name, value)

    def __delattr__(self, name):
        delattr(self.wrapped, name)

    def __str__(self):
        return str(self.wrapped)

    def __repr__(self):
        return repr(self.wrapped)



