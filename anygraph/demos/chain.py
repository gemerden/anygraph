from anygraph import One


class Chained(object):
    next = One('prev')
    prev = One('next')


if __name__ == '__main__':
    bob = Chained()
    ann = Chained()
    pip = Chained()

    bob.next = ann
    ann.next = pip

    assert ann.prev is bob
    assert pip.prev is ann

    del pip.prev
    assert ann.next is None



