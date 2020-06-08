import unittest

from anygraph import Many, One, Gather, Iterator, GetEndpoints


class TestPropagator(unittest.TestCase):
    class TestMany(object):
        nexts = Many('prevs')
        prevs = Many('nexts')

        def __init__(self, name):
            self.name = name

    def create_objects(self, count=10):
        objs = [self.TestMany('bob_' + str(i)) for i in range(count)]
        for i, obj in enumerate(objs):
            for next_obj in objs[i+1:]:
                obj.nexts.add(next_obj)
        return objs

    def back_wire(self, objs):
        for obj1 in objs:
            for obj2 in objs:
                if obj2 in obj1.nexts:
                    obj2.nexts.add(obj1)

    def test_iterate(self):
        count = 10
        objs = self.create_objects(count)
        for breadth_first in [False, True]:
            iterator = Iterator('nexts')
            assert len(list(iterator.iterate(objs[0], breadth_first=breadth_first))) == count

            iterator = Iterator('prevs')
            assert len(list(iterator.iterate(objs[count-1], breadth_first=breadth_first))) == count

    def test_propagate(self):
        count = 10
        objs = self.create_objects(count)

        next_gatherer = Gather('nexts')
        assert len(next_gatherer(objs[0])) == count
        assert len(next_gatherer(objs[1])) == count-1

        prev_gatherer = Gather('prevs')
        assert len(prev_gatherer(objs[count-1])) == count
        assert len(prev_gatherer(objs[count-2])) == count-1

        self.back_wire(objs)

        next_gatherer = Gather('nexts')
        assert len(next_gatherer(objs[count-1])) == count
        assert len(next_gatherer(objs[count//2])) == count

    def test_endpoint(self):
        class StartPoint(object):
            next = One('prev')

        class EndPoint(object):
            prev = One('next')

        start = StartPoint()
        endpt = EndPoint()
        start.next = endpt

        next_gatherer = Gather('next')
        nodes = next_gatherer(start)
        assert len(nodes) == 2

        get_endpoints = GetEndpoints('next')
        assert get_endpoints(start) == [endpt]




