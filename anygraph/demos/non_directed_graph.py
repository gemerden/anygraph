from anygraph import Many


class Friend(object):
    friends = Many('friends')


if __name__ == '__main__':
    bob = Friend()
    ann = Friend()
    pip = Friend()

    bob.friends = [ann, pip]
    assert bob in pip.friends
    assert ann not in pip.friends
