import random

from anygraph import Many
from anygraph.tools import flipcoin


class Person(object):
    friends = Many('friends')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


if __name__ == '__main__':
    """ lets make some potential friends """
    bob = Person('bob')
    ann = Person('ann')
    pip = Person('pip')
    kik = Person('kik')
    tom = Person('tom')
    rob = Person('rob')
    jan = Person('jan')

    peeps = [bob, ann, pip, kik, tom, rob, jan]

    """ anyone has about 1/3 of the others as friends """
    for p1 in peeps:
        for p2 in peeps:
            if p1 is not p2 and flipcoin(1/3):
                p1.friends.include(p2)

    """ lets see what we got """
    for person in peeps:
        print(person, ':', person.friends)
    print()

    """ here we iterate through the graph starting with 'bob' depth-first avoiding cycles """
    print('depth first:  ', list(Person.friends.iterate(bob)))

    """ same but breadth first iteration """
    print('breadth first:', list(Person.friends.iterate(bob, breadth_first=True)))

    """ same again but now cyclic and with a break """
    print('\ncyclic iteration:')
    for i, peep in enumerate(Person.friends.iterate(bob, cyclic=True, breadth_first=True)):
        if i >= 10:
            break
        print(i, peep)
    print()

    """ lets gather the peeps with a name with middle character 'o' """
    o_peeps = []

    def visit(person):
        if person.name[1] == 'o':
            o_peeps.append(person)

    Person.friends.visit(bob, on_visit=visit)
    print("people with an 'o' in the middle:", o_peeps)

    """ see whether jan is in the network of bob """
    print('reachable:', Person.friends.reachable(bob, jan))

    """ see whether jan is part of a cycle in the graph """
    print('in cycle:', Person.friends.in_cycle(jan))

    """ randomly walk through the graph (indefinitely if not stopped) """
    print('\nrandom walk:')
    for i, peep in enumerate(Person.friends.walk(ann, key=lambda p: random.choice(list(p.friends)))):
        if i >= 10:
            break
        print(i, peep)


