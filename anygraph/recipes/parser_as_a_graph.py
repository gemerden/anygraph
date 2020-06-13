"""
Here we will show a parser for a simple calculator doing calculation like 3 + (4 - 2) / 2.
Preference rules (first multiply then sum) ae not included.

Disclaimer: I don't often write parsers, so terminology might be off.

Note that we use a ManyMap to be able to do lookups in the next nodes in the graph
"""
from anygraph import ManyMap


class SyntaxError(ValueError):
    pass


class Token(object):
    nexts = ManyMap('prevs', get_id=lambda t: t.char)  # double linked for easier syntax definition
    prevs = ManyMap('nexts', get_id=lambda t: t.char)  # define get_id to define tokens by their character

    @classmethod
    def valid(cls, item):
        raise NotImplementedError

    def __init__(self, char):
        self.char = char

    def __str__(self):
        return self.char


class Operator(Token):
    operators = '+-*/'

    @classmethod
    def create(cls):
        return {c: Operator(c) for c in cls.operators}

    @classmethod
    def valid(cls, item):
        if item in cls.operators:
            return item
        raise SyntaxError(f"'{item}' is not an operator")


class Variable(Token):

    @classmethod
    def valid(cls, item):
        if item.isalpha():
            return '_'
        raise SyntaxError(f"'{item}' is not ASCII")


parentheses = '()'

""" create tokens """
def create_operator_tokens(chars):
    return {char: Operator(char) for char in chars}  # use dict for easy lookup


""" what tokens can follow each other in a valid expression; create the 'syntax' rules """


class Calculator(object):
    tokens = Operator.create()
    tokens['_'] = Variable('_')

    tokens['_'].nexts = [tokens['+'], tokens['-'], tokens['*'], tokens['/']]
    tokens['_'].prevs = [tokens['+'], tokens['-'], tokens['*'], tokens['/']]

    def __init__(self):
        self.index = 0
        self.char_list = None

    def tokenize(self, string):
        return [s.strip() for s in string.split(' ') if len(s)]

    def get_token(self, char):
        try:
            return self.tokens[Operator.valid(char)]
        except SyntaxError:
            return self.tokens[Variable.valid(char)]

    def key(self, token):
        """ make sure the next character """
        self.index += 1
        try:
            next_chars = self.char_list[self.index]
        except IndexError:
            return None
        else:
            try:
                valid_char = Operator.valid(next_chars)
            except SyntaxError:
                valid_char = Variable.valid(next_chars)
            try:
                return token.nexts[valid_char]
            except KeyError:
                raise SyntaxError(f"'{self.char_list[self.index-1]}' before '{valid_char}'")

    def is_valid(self, string):
        self.index = 0
        self.char_list = self.tokenize(string)
        start_token = self.get_token(self.char_list[0])
        try:
            for _ in Token.nexts.walk(start_token, key=self.key, on_visit=lambda t: print(t)):
                pass
        except SyntaxError:
            return False
        else:
            return True


calc = Calculator()
print(calc.is_valid("a + b - c"))
print(calc.is_valid("a + b x c"))


#
# tokens['('].nexts = [tokens['#']]
# tokens['('].prevs = [tokens['+'], tokens['-'], tokens['*'], tokens['/']]
#














