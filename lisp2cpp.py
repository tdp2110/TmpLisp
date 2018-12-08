import re
import sys
from enum import Enum


LPAREN = '('
RPAREN = ')'
QUOTE_LPAREN = '\'('

class Ops(Enum):
    Add = '+'
    Sub = '-'
    Mul = '*'
    Eq = '='
    Neq = '!='
    Leq = '<='
    Or = 'or'
    And = 'and'
    Not = 'not'
    Cons = 'cons'
    Car = 'car'
    Cdr = 'cdr'
    IsNull = 'null?'

class Keywords(Enum):
    Lambda = 'lambda'
    
class Var:
    def __init__(self, val):
        # match some regex
        self.val = val

    def __eq__(self, other):
        return self.val == other.val

    def __str__(self):
        return 'Var({})'.format(self.value)

class Int:
    def __init__(self, val):
        if isinstance(val, int) or re.match('^[-+]?[0-9]+$', val):
            self.val = int(val)
        else:
            raise ValueError

    def __eq__(self, other):
        return self.val == other.val

class Tokenizer:
    def __init__(self, text):
        self.tokens = list(self.tokenize(text))

    def cur_tok(self):
        return self.tokens[0]

    def peek(self):
        return self.tokens[1]

    def pop(self):
        self.tokens.pop(0)

    @staticmethod
    def classify_item(item):
        if item == LPAREN or item == RPAREN:
            return item
        try:
            return Ops(item)
        except ValueError:
            try:
                return Keywords(item)
            except ValueError:
                try:
                    return Int(item)
                except Exception:
                    #TODO need some regex for variables
                    return Var(item)
        
    @classmethod
    def tokenize_chunk(cls, chunk):
        m = re.match('([\(]*)([^\(\)]*)([\)]*)$', chunk)

        if m:
            for group in m.groups():
                if group:
                    if group[0] == LPAREN or group[0] == RPAREN:
                        yield from group
                    else:
                        yield cls.classify_item(group)
        m = re.match('^\'\((.*)', chunk)

        if m:
            yield QUOTE_LPAREN
            group = m.groups()[0]
            if group:
                yield from cls.tokenize(group)

    @classmethod
    def tokenize(cls, text):
        for chunk in text.split():
            yield from cls.tokenize_chunk(chunk)

class Parser:
    @classmethod
    def parse(cls, txt):
        tokenizer = Tokenizer(text)
        return cls(tokenizer).parse()

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def parse(self):
        pass
            
def main():
    lines = sys.stdin.readlines()
    tokens = Tokenizer(''.join(lines)).tokens
    print('\n'.join(tokens))    
    
if __name__ == '__main__':
    main()
