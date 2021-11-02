import unittest

from anygraph import One, ManyMap

class TestLinkers(unittest.TestCase):

    def test_many(self):
        class TestMany(object):
            nexts = ManyMap()

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        assert list(bob.nexts) == ['ann', 'pete']

        bob.nexts.rekey('ann', 'ann2')

        assert list(bob.nexts) == ['ann2', 'pete']

        assert bob.nexts.get_key(pete) == 'pete'
        assert bob.nexts.get_key(ann) == 'ann2'

        assert ann in bob.nexts.values()
        assert howy in pete.nexts.values()
        assert howy not in bob.nexts.values()

        assert list(TestMany.nexts.iterate(bob)) == [bob, ann, pete, howy]

    def test_cyclic(self):
        class TestMany(object):
            nexts = ManyMap(cyclic=False)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        with self.assertRaises(ValueError):
            howy.nexts.include(bob)

    def test_on_link(self):
        on_link_results = []
        on_unlink_results = []

        def on_link(one, two):
            on_link_results.append((one, two))

        def on_unlink(one, two):
            on_unlink_results.append((one, two))

        class TestMany(object):
            nexts = ManyMap(on_link=on_link, on_unlink=on_unlink)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        assert on_link_results == [(bob, ann), (bob, pete), (pete, howy)]

        del bob.nexts
        assert on_unlink_results == [(bob, ann), (bob, pete)]

    def test_visitor(self):
        class TestMany(object):
            nexts = ManyMap()

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        ann.nexts.include(howy)
        pete.nexts.include(howy)

        people = []

        def on_visit(obj):
            people.append(obj)

        TestMany.nexts.visit(bob, on_visit=on_visit, breadth_first=False)
        assert people == [bob, ann, howy, pete]

        del people[:]
        TestMany.nexts.visit(bob, on_visit=on_visit, breadth_first=True)
        assert people == [bob, ann, pete, howy]

    def test_builder_many_by_name(self):

        class TestBuilder(object):
            nexts = ManyMap()

            def __init__(self, name, iterable=()):
                self.name = name
                self.items = list(iterable)

            def extend(self, *items):
                self.items.extend(items)

            def __iter__(self):
                for item in self.items:
                    yield item

        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pete = TestBuilder('pete')
        howy = TestBuilder('howy')

        bob.extend(ann, pete)
        pete.extend(howy, bob)
        ann.extend(pete)
        howy.extend(ann)

        assert bob.nexts == {}

        TestBuilder.nexts.build(bob)

        assert bob.nexts == dict(ann=ann, pete=pete)
        assert howy.nexts == dict(ann=ann)

    def test_builder_many_by_func_cyclic(self):

        class TestBuilder(object):
            nexts = ManyMap()

            def __init__(self, name, iterable=()):
                self.name = name
                self.items = list(iterable)

            def extend(self, *items):
                self.items.extend(items)

        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pete = TestBuilder('pete')
        howy = TestBuilder('howy')

        bob.extend(ann, pete)
        pete.extend(howy, bob)
        ann.extend(pete)
        howy.extend(ann)

        TestBuilder.nexts.build(bob, key=lambda obj: obj.items)

        assert pete.nexts == dict(howy=howy, bob=bob)
        assert howy.nexts == dict(ann=ann)
        assert TestBuilder.nexts.in_cycle(bob)
        assert TestBuilder.nexts.is_cyclic(bob)

    def test_builder_one(self):

        class TestBuilder(object):
            next = One()

            def __init__(self, name, other=None):
                self.name = name
                self.other = other

            def __str__(self):
                return self.name

        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pip = TestBuilder('pip')

        bob.other = ann
        ann.other = pip

        assert bob.next is None

        TestBuilder.next.build(bob, 'other')

        assert bob.next == ann
        assert ann.next == pip


class TestDoubleLinkers(unittest.TestCase):

    def test_many_many(self):
        class TestMany(object):
            nexts = ManyMap('prevs')
            prevs = ManyMap('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        assert ann in bob.nexts.values()
        assert bob in ann.prevs.values()
        assert howy in pete.nexts.values()
        assert howy not in bob.nexts.values()

        assert list(TestMany.nexts.iterate(bob)) == [bob, ann, pete, howy]

    def test_one_many(self):
        class TestOneMany(object):
            parent = One('children')
            children = ManyMap('parent')

            def __init__(self, name):
                self.name = name

        bob = TestOneMany('bob')
        ann = TestOneMany('ann')
        pete = TestOneMany('pete')
        howy = TestOneMany('howy')

        bob.children = [ann, pete]
        howy.parent = pete

        assert ann in bob.children.values()
        assert bob is ann.parent
        assert howy in pete.children.values()
        assert howy not in bob.children.values()
        assert howy.parent.parent is bob

        assert list(TestOneMany.children.iterate(bob)) == [bob, ann, pete, howy]
        assert list(TestOneMany.parent.iterate(howy)) == [howy, pete, bob]

        del bob.children

        assert ann not in bob.children
        assert bob is not ann.parent
        assert howy.parent.parent is None

    def test_pairs(self):
        class Test(object):
            other = One('other')

            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        bob = Test('bob')
        ann = Test('ann')
        kik = Test('kik')

        bob.other = ann
        assert bob.other is ann
        assert ann.other is bob

        assert list(Test.other.iterate(bob)) == [bob, ann]

        kik.other = ann
        assert bob.other is None
        assert kik.other is ann
        assert ann.other is kik

    def test_non_directed(self):
        class Test(object):
            others = ManyMap('others')

            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        bob = Test('bob')
        ann = Test('ann')
        kik = Test('kik')

        bob.others.include(ann)
        bob.others.include(kik)
        assert ann in bob.others.values()
        assert kik in bob.others.values()
        assert bob in ann.others.values()
        assert bob in kik.others.values()

        kik.others.include(ann)
        assert kik in ann.others.values()
        assert ann in kik.others.values()
        assert ann in bob.others.values()
        assert kik in bob.others.values()
        assert bob in ann.others.values()
        assert bob in kik.others.values()

        assert list(Test.others.iterate(bob)) == [bob, ann, kik]

        kik.others.exclude(ann)
        assert kik not in ann.others.values()
        assert ann not in kik.others.values()
        assert ann in bob.others.values()
        assert kik in bob.others.values()
        assert bob in ann.others.values()
        assert bob in kik.others.values()

    def test_cyclic(self):
        class TestMany(object):
            nexts = ManyMap('prevs', cyclic=False)
            prevs = ManyMap('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        with self.assertRaises(ValueError):
            howy.nexts.include(bob)

        with self.assertRaises(ValueError):
            bob.prevs.include(howy)



    def test_on_link(self):
        on_link_results = []
        on_unlink_results = []

        def on_link(one, two):
            on_link_results.append((one, two))

        def on_unlink(one, two):
            on_unlink_results.append((one, two))

        class TestMany(object):
            nexts = ManyMap('prevs', on_link=on_link, on_unlink=on_unlink)
            prevs = ManyMap('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        assert on_link_results == [(bob, ann), (bob, pete), (pete, howy)]

        del bob.nexts
        assert on_unlink_results == [(bob, ann), (bob, pete)]

    def test_visitor(self):
        class TestMany(object):
            nexts = ManyMap('prevs')
            prevs = ManyMap('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.include(ann, pete)
        ann.nexts.include(howy)
        pete.nexts.include(howy)

        people = []

        def on_visit(obj):
            people.append(obj)

        TestMany.nexts.visit(bob, on_visit=on_visit, breadth_first=False)
        assert people == [bob, ann, howy, pete]

        del people[:]
        TestMany.nexts.visit(bob, on_visit=on_visit, breadth_first=True)
        assert people == [bob, ann, pete, howy]

    def test_builder_many_by_name(self):

        class TestBuilder(object):
            nexts = ManyMap('prevs')
            prevs = ManyMap('nexts')

            def __init__(self, name, iterable=()):
                self.name = name
                self.items = list(iterable)

            def extend(self, *items):
                self.items.extend(items)

            def __iter__(self):
                for item in self.items:
                    yield item

            def __str__(self):
                return self.name



        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pete = TestBuilder('pete')
        howy = TestBuilder('howy')

        bob.extend(ann, pete)
        pete.extend(howy, bob)
        ann.extend(pete)
        howy.extend(ann)

        assert bob.nexts == {}
        assert ann.prevs == {}

        TestBuilder.nexts.build(bob)

        assert bob.nexts == dict(ann=ann, pete=pete)
        assert ann.prevs == dict(bob=bob, howy=howy)
        assert howy.nexts == dict(ann=ann)
        assert howy.prevs == dict(pete=pete)

    def test_builder_many_by_func(self):

        class TestBuilder(object):
            nexts = ManyMap('prevs')
            prevs = ManyMap('nexts')

            def __init__(self, name, iterable=()):
                self.name = name
                self.items = list(iterable)

            def extend(self, *items):
                self.items.extend(items)

            def __str__(self):
                return self.name



        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pete = TestBuilder('pete')
        howy = TestBuilder('howy')

        bob.extend(ann, pete)
        pete.extend(howy, bob)
        ann.extend(pete)
        howy.extend(ann)

        assert bob.nexts == dict()
        assert ann.prevs == dict()

        TestBuilder.nexts.build(bob, key=lambda obj: obj.items)

        assert bob.nexts == dict(ann=ann, pete=pete)
        assert ann.prevs == dict(bob=bob, howy=howy)
        assert howy.nexts == dict(ann=ann)
        assert howy.prevs == dict(pete=pete)

    def test_builder_one(self):

        class TestBuilder(object):
            next = One('prev')
            prev = One('next')

            def __init__(self, name, other=None):
                self.name = name
                self.other = other

            def __str__(self):
                return self.name

        bob = TestBuilder('bob')
        ann = TestBuilder('ann')
        pip = TestBuilder('pip')

        bob.other = ann
        ann.other = pip

        assert bob.next is None
        assert ann.prev is None

        TestBuilder.next.build(bob, 'other')

        assert bob.next == ann
        assert ann.prev == bob
        assert ann.next == pip
        assert pip.prev == ann

    def test_gather(self):
        class Test(object):
            nexts = ManyMap('prevs')
            prevs = ManyMap('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        bob = Test('bob')
        ann = Test('ann')
        pete = Test('pete')
        howy = Test('howy')

        bob.nexts.include(ann)
        ann.prevs.include(pete)
        pete.nexts.include(howy, bob)

        assert Test.nexts.gather(bob) == [bob, ann, pete, howy]






