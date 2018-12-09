from collections import namedtuple
import re
import sys
from enum import Enum


LPAREN = '('
RPAREN = ')'
QUOTE_LPAREN = '\'('
LAMBDA = 'lambda'
SEMICOLON = ';'

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
    Lambda = LAMBDA
    
class Var:
    def __init__(self, val):
        # match some regex
        self.val = val

    def __eq__(self, other):
        try:
            return self.val == other.val
        except AttributeError:
            return self.val == other

    def __str__(self):
        return 'Var({})'.format(self.value)

class Int:
    def __init__(self, val):
        if isinstance(val, int) or re.match('^[-+]?[0-9]+$', val):
            self.val = int(val)
        else:
            raise ValueError

    def __eq__(self, other):
        try:
            return self.val == other.val
        except AttributeError:
            return self.val == other

class Tokenizer:
    def __init__(self, text):
        self.tokens = list(self.tokenize(text))

    def top(self):
        return self.tokens[0]

    def peek(self):
        return self.tokens[1]

    def pop(self):
        self.tokens.pop(0)

    def num_tokens(self):
        return len(self.tokens)

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
                    assert re.match('^[a-zA-Z_]+[a-zA-Z_0-9\!\-\?]*$', item), (item, type(item))
                    return Var(item)
        
    @classmethod
    def tokenize_chunk(cls, chunk):
        m = re.match('^([\)\(]+)(.*)$', chunk)

        if m:
            leading_parens = m.groups()[0]
            yield from leading_parens

            rest = m.groups()[1]
            if rest:
                yield from cls.tokenize_chunk(rest)

            return
        
        m = re.match('^\'\((.*)$', chunk)

        if m:
            yield QUOTE_LPAREN
            group = m.groups()[0]
            if group:
                yield from cls.tokenize(group)

            return

        m = re.match('^([^\(\);]+)(.*)$', chunk)

        if m:
            yield cls.classify_item(m.groups()[0])
            rest = m.groups()[1]
            if rest:
                yield from cls.tokenize_chunk(rest)

            return

        if chunk[0] == SEMICOLON:
            return

    @classmethod
    def tokenize(cls, text):
        for chunk in text.split():
            yield from cls.tokenize_chunk(chunk)        

            
SExp = namedtuple('SExp', ['operator', 'operands'])
LambdaExp = namedtuple('LambdaExp', ['arglist', 'body'])


class Parser:
    @classmethod
    def parse(cls, text):
        tokenizer = Tokenizer(text)
        return cls(tokenizer).parse_exp()

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def parse_item(self):
        if self.tokenizer.top() == LPAREN:
            self.tokenizer.pop()
            if self.tokenizer.top() == Keywords.Lambda:
                self.tokenizer.pop()
                res = self.parse_lambda()
            else:
                res = self.parse_s_exp_body()
            assert self.tokenizer.top() == RPAREN
            self.tokenizer.pop()
        elif self.tokenizer.top() == LAMBDA:
            self.tokenizer.pop()
            res = self.parse_lambda()
        else:
            res = self.parse_atom()

        return res

    def parse_exp(self):
        res = self.parse_item()
        assert self.tokenizer.num_tokens() == 0
        return res

    def parse_lambda(self):
        def parse_arglist():
            assert self.tokenizer.top() == LPAREN
            self.tokenizer.pop()
            res = []
            while self.tokenizer.top() != RPAREN:
                assert isinstance(self.tokenizer.top(),
                                  Var)
                res.append(self.tokenizer.top())
                self.tokenizer.pop()
            self.tokenizer.pop()
            return res
                
        def parse_body():
            return self.parse_item()
        
        return LambdaExp(
            arglist=parse_arglist(),
            body=parse_body())
    
    def parse_atom(self):
        next_tok = self.tokenizer.top()

        if isinstance(next_tok, (Var, Int, Ops)):
            self.tokenizer.pop()
            return next_tok

        assert False, next_tok
        
    def parse_s_exp_body(self):
        operator = self.parse_item()
        operands = []
        while self.tokenizer.top() != RPAREN:
            operands.append(self.parse_item())

        return SExp(operator=operator,
                    operands=operands)
            
def main():
    lines = sys.stdin.readlines()
    tokens = Tokenizer(''.join(lines)).tokens
    print('\n'.join(tokens))    
    
if __name__ == '__main__':
    main()
