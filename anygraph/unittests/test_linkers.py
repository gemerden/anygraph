import unittest
from random import choice

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

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

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

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

        with self.assertRaises(ValueError):
            howy.nexts.include(bob)

    def test_to_self(self):
        class TestMany(object):
            nexts = Many(to_self=False)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')

        with self.assertRaises(ValueError):
            bob.nexts.include(bob)

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

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

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

        bob.nexts.include(ann, pete)
        pete.nexts.include(howy)

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

        bob.others.include(ann)
        bob.others.include(kik)
        assert ann in bob.others
        assert kik in bob.others
        assert bob in ann.others
        assert bob in kik.others

        kik.others.include(ann)
        assert kik in ann.others
        assert ann in kik.others
        assert ann in bob.others
        assert kik in bob.others
        assert bob in ann.others
        assert bob in kik.others

        assert list(Test.others.iterate(bob)) == [bob, ann, kik]

        kik.others.exclude(ann)
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
            nexts = Many('prevs', on_link=on_link, on_unlink=on_unlink)
            prevs = Many('nexts')

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
            nexts = Many('prevs')
            prevs = Many('nexts')

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

        bob.nexts.include(ann)
        ann.prevs.include(pete)
        pete.nexts.include(howy, bob)

        print(Test.nexts.gather(bob))

        assert Test.nexts.gather(bob) == [bob, ann, pete, howy]

    def test_gather_pairs_directed(self):

        class Test(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(str(i)) for i in range(5)]

        for node in nodes:  # fully linked
            node.nexts.include(*nodes)

        assert len(nodes[0].nexts) == 5
        assert len(nodes[0].prevs) == 5

        nexts_pairs = Test.nexts.gather_pairs(nodes[0])
        assert len(nexts_pairs) == 25

        prevs_pairs = Test.prevs.gather_pairs(nodes[0])
        assert len(prevs_pairs) == 25

    def test_gather_pairs_non_directed(self):

        class Test(object):
            friends = Many('friends')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(str(i)) for i in range(5)]

        for node in nodes:  # fully linked
            node.friends.include(*nodes)

        assert len(nodes[0].friends) == 5

        nexts_pairs = Test.friends.gather_pairs(nodes[0])
        assert len(nexts_pairs) == 25

    def test_find_directed(self):

        class Test(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if (i + j) % 2 == 1:
                    node1.nexts.include(node2)

        found = Test.nexts.find(nodes[0], filter=lambda n: n.name in (1, 2))
        assert len(found) == 2

    def test_find_non_directed(self):

        class Test(object):
            friends = Many('friends')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if (i + j) % 2 == 1:
                    node1.friends.include(node2)

        found = Test.friends.find(nodes[0], filter=lambda n: n.name in (1, 2))
        assert len(found) == 2

    def test_reachable_directed(self):

        class Test(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if j == i + 1:
                    node1.nexts.include(node2)

        reachable = Test.nexts.reachable(nodes[0], nodes[4])
        assert reachable

        reachable = Test.nexts.reachable(nodes[1], nodes[0])
        assert not reachable

    def test_reachable_non_directed(self):

        class Test(object):
            friends = Many('friends')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if j == i + 1:
                    node1.friends.include(node2)

        reachable = Test.friends.reachable(nodes[0], nodes[4])
        assert reachable

        reachable = Test.friends.reachable(nodes[1], nodes[0])
        assert reachable

    def test_walk_directed(self):

        class Test(object):
            nexts = Many('prevs')
            prevs = Many('nexts')

            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if j in (i + 1, i + 2):
                    node1.nexts.include(node2)

        visited = list(Test.nexts.walk(nodes[0], key=lambda n: n.nexts[0] if len(n.nexts) else None))
        assert visited == nodes

    def test_walk_non_directed(self):

        class Test(object):
            friends = Many('friends')

            def __init__(self, name):
                self.name = str(name)

            def __repr__(self):
                return self.name

        nodes = [Test(i) for i in range(5)]

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if j in (i + 1, i + 2):
                    node1.friends.include(node2)

        visited = []
        for node in Test.friends.walk(nodes[0], key=lambda n: n.friends[0]):
            visited.append(node)
            if len(visited) == 5:
                break

        print(visited)
        assert len(set(visited)) == 2

    def test_install_one(self):
        class TestMany(object):
            one = One('one', install=True)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')

        bob.one = ann

        assert ann.one is bob
        assert bob.one is ann

        assert bob.iterate.__name__ == 'iterate'
        assert list(bob.iterate()) == [bob, ann]

        assert bob.shortest_path.__name__ == 'shortest_path'
        assert bob.shortest_path(ann) == [bob, ann]
        assert bob.in_cycle()

    def test_install_many(self):
        class TestMany(object):
            nexts = Many(install=True)

            def __init__(self, name):
                self.name = name

        bob = TestMany('bob')
        ann = TestMany('ann')

        bob.nexts.include(ann)
        ann.nexts.include(bob)

        assert ann in bob.nexts
        assert bob in ann.nexts

        assert bob.iterate.__name__ == 'iterate'
        assert list(bob.iterate()) == [bob, ann]

        assert bob.shortest_path.__name__ == 'shortest_path'
        assert bob.shortest_path(ann) == [bob, ann]
        assert bob.in_cycle()

    def test_install_non_directed(self):

        class Friend(object):
            friends = Many('friends', install=True)

            def __init__(self, name):
                self.name = name

        bob = Friend('bob')
        ann = Friend('ann')

        bob.friends.include(ann)

        assert ann in bob.friends
        assert bob in ann.friends

        assert bob.iterate.__name__ == 'iterate'
        assert list(bob.iterate()) == [bob, ann]

        assert bob.shortest_path.__name__ == 'shortest_path'
        assert ann.shortest_path(bob) == [ann, bob]
        assert bob.in_cycle()

    def test_directed_image(self):
        names = ('ann', 'bob', 'fred', 'betty', 'eric', 'charley', 'claudia', 'lars', 'jan')

        class Object(object):
            nexts = Many(install=True)

            def __init__(self, key):
                self.key = key

        nodes = [Object(name) for name in names]

        for _ in range(20):
            choice(nodes).nexts.include(choice(nodes))

        try:
            nodes[0].save_image('/data/nexts.png', label_getter=lambda obj: obj.key, view=False)
        except RuntimeError as error:  # graphviz not installed
            print(error)

    def test_undirected_image(self):

        names = ('ann', 'bob', 'fred', 'betty', 'eric', 'charley', 'claudia', 'lars', 'jan', 'imogen')  # len() == 10

        class Person(object):
            friends = Many('friends', install=True)

            def __init__(self, name):
                self.name = name

        nodes = [Person(name) for name in names]

        for _ in range((len(names)*len(names))//3):
            person1 = choice(nodes)
            person2 = choice(nodes)
            if person1 is not person2:
                person1.friends.include(person2)

        try:
            nodes[0].save_image('/data/friends.png', label_getter=lambda obj: obj.name, view=False)
        except RuntimeError as error:  # graphviz not installed
            print(error)




