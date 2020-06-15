import unittest

from anygraph import One, Many

class TestLinkers(unittest.TestCase):

    def test_one(self):
        class TestOne(object):
            next = One()

            def __init__(self, name):
                self.name = name

        bob = TestOne('bob')
        ann = TestOne('ann')

        bob.next = ann
        assert bob.next is ann

        assert list(TestOne.next.iterate(bob)) == [bob, ann]

        del bob.next
        assert bob.next is None

        bob.next = ann
        ann.next = bob
        assert bob.next is ann
        assert ann.next is bob

        bob.next = bob
        assert bob.next is bob

    def test_triangle(self):
        class TestOne(object):
            next = One()

            def __init__(self, name):
                self.name = name

        bob = TestOne('bob')
        ann = TestOne('ann')
        kik = TestOne('kik')

        bob.next = ann
        ann.next = kik
        kik.next = bob

        assert bob.next is ann
        assert ann.next is kik
        assert kik.next is bob

        assert list(TestOne.next.iterate(bob)) == [bob, ann, kik]

        del ann.next

        assert ann.next is None
        assert bob.next is ann
        assert kik.next is bob

    def test_many(self):
        class TestMany(object):
            nexts = Many()

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        assert ann in bob.nexts
        assert howy in pete.nexts
        assert howy not in bob.nexts

        assert list(TestMany.nexts.iterate(bob)) == [bob, ann, pete, howy]

    def test_cyclic(self):
        class TestMany(object):
            nexts = Many(cyclic=False)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        with self.assertRaises(ValueError):
            howy.nexts.add(bob)

    def test_to_self(self):
        class TestMany(object):
            nexts = Many(to_self=False)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')

        with self.assertRaises(ValueError):
            bob.nexts.add(bob)

        with self.assertRaises(ValueError):
            bob.nexts = [bob]


    def test_on_link(self):
        on_link_results = []
        on_unlink_results = []

        def on_link(one, two):
            on_link_results.append((one, two))

        def on_unlink(one, two):
            on_unlink_results.append((one, two))

        class TestMany(object):
            nexts = Many(on_link=on_link, on_unlink=on_unlink)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        assert on_link_results == [(bob, ann), (bob, pete), (pete, howy)]

        del bob.nexts
        assert on_unlink_results == [(bob, ann), (bob, pete)]

    def test_visitor(self):
        class TestMany(object):
            nexts = Many()

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        ann.nexts.add(howy)
        pete.nexts.add(howy)

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
            nexts = Many()

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

        assert bob.nexts == set()

        TestBuilder.nexts.build(bob)

        assert bob.nexts == {ann, pete}
        assert howy.nexts == {ann}

    def test_builder_many_by_func_cyclic(self):

        class TestBuilder(object):
            nexts = Many()

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

        assert bob.nexts == {ann, pete}
        assert pete.nexts == {howy, bob}
        assert howy.nexts == {ann}
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

    def test_one_one(self):
        class TestOneOne(object):
            left = One('right')
            right = One('left')

            def __init__(self, name):
                self.name = name

        bob = TestOneOne('bob')
        ann = TestOneOne('ann')

        bob.left = ann
        assert bob.left is ann
        assert ann.right is bob

        assert list(TestOneOne.left.iterate(bob)) == [bob, ann]

        del bob.left
        assert bob.left is None
        assert ann.right is None

        bob.left = ann
        ann.right = None
        assert bob.left is None
        assert ann.right is None

        bob.left = bob
        assert bob.left is bob
        assert bob.right is bob

        del bob.left
        assert bob.left is None
        assert bob.right is None

    def test_triangle(self):
        class TestOne(object):
            next = One('prev')
            prev = One('next')

            def __init__(self, name):
                self.name = name

        bob = TestOne('bob')
        ann = TestOne('ann')
        kik = TestOne('kik')

        bob.next = ann
        ann.next = kik
        kik.next = bob

        assert bob.next is ann
        assert ann.next is kik
        assert kik.next is bob

        assert bob.prev is kik
        assert kik.prev is ann
        assert ann.prev is bob

        assert list(TestOne.next.iterate(bob)) == [bob, ann, kik]

        del ann.prev

        assert ann.prev is None
        assert bob.next is None
        assert ann.next is kik
        assert kik.next is bob

    def test_many_many(self):
        class TestMany(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        assert ann in bob.nexts
        assert bob in ann.prevs
        assert howy in pete.nexts
        assert howy not in bob.nexts

        assert list(TestMany.nexts.iterate(bob)) == [bob, ann, pete, howy]

    def test_one_many(self):
        class TestOneMany(object):
            parent = One('children')
            children = Many('parent')

            def __init__(self, name):
                self.name = name

        bob = TestOneMany('bob')
        ann = TestOneMany('ann')
        pete = TestOneMany('pete')
        howy = TestOneMany('howy')

        bob.children = [ann, pete]
        howy.parent = pete

        assert ann in bob.children
        assert bob is ann.parent
        assert howy in pete.children
        assert howy not in bob.children
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
            others = Many('others')

            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        bob = Test('bob')
        ann = Test('ann')
        kik = Test('kik')

        bob.others.add(ann)
        bob.others.add(kik)
        assert ann in bob.others
        assert kik in bob.others
        assert bob in ann.others
        assert bob in kik.others

        kik.others.add(ann)
        assert kik in ann.others
        assert ann in kik.others
        assert ann in bob.others
        assert kik in bob.others
        assert bob in ann.others
        assert bob in kik.others

        assert list(Test.others.iterate(bob)) == [bob, ann, kik]

        kik.others.remove(ann)
        assert kik not in ann.others
        assert ann not in kik.others
        assert ann in bob.others
        assert kik in bob.others
        assert bob in ann.others
        assert bob in kik.others

    def test_cyclic(self):
        class TestMany(object):
            nexts = Many('prevs', cyclic=False)
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        with self.assertRaises(ValueError):
            howy.nexts.add(bob)

        with self.assertRaises(ValueError):
            bob.prevs.add(howy)



    def test_on_link(self):
        on_link_results = []
        on_unlink_results = []

        def on_link(one, two):
            on_link_results.append((one, two))

        def on_unlink(one, two):
            on_unlink_results.append((one, two))

        class TestMany(object):
            nexts = Many('prevs', on_link=on_link, on_unlink=on_unlink)
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        pete.nexts.add(howy)

        assert on_link_results == [(bob, ann), (bob, pete), (pete, howy)]

        del bob.nexts
        assert on_unlink_results == [(bob, ann), (bob, pete)]

    def test_visitor(self):
        class TestMany(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')
        pete = TestMany('pete')
        howy = TestMany('howy')

        bob.nexts.update([ann, pete])
        ann.nexts.add(howy)
        pete.nexts.add(howy)

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
            nexts = Many('prevs')
            prevs = Many('nexts')

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

        assert bob.nexts == set()
        assert ann.prevs == set()

        TestBuilder.nexts.build(bob)

        assert bob.nexts == {ann, pete}
        assert ann.prevs == {bob, howy}
        assert howy.nexts == {ann}
        assert howy.prevs == {pete}

    def test_builder_many_by_func(self):

        class TestBuilder(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

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

        assert bob.nexts == set()
        assert ann.prevs == set()

        TestBuilder.nexts.build(bob, key=lambda obj: obj.items)

        assert bob.nexts == {ann, pete}
        assert ann.prevs == {bob, howy}
        assert howy.nexts == {ann}
        assert howy.prevs == {pete}

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
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        bob = Test('bob')
        ann = Test('ann')
        pete = Test('pete')
        howy = Test('howy')

        bob.nexts.add(ann)
        ann.prevs.add(pete)
        pete.nexts.update([howy, bob])

        print(Test.nexts.gather(bob))

        assert Test.nexts.gather(bob) == [bob, ann, pete, howy]






