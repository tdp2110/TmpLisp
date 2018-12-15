
#  Restricted Scheme-like Language using Template Metaprogramming
#
#  Copyright Thomas D Peters 2018-present
#
#  Use, modification and distribution is subject to the
#  Boost Software License, Version 1.0. (See accompanying
#  file LICENSE or copy at
#  http://www.boost.org/LICENSE_1_0.txt)

import argparse
from collections import namedtuple
from enum import Enum
import os
import sys
import re


LPAREN = '('
RPAREN = ')'
QUOTE = '\''
LAMBDA = 'lambda'
SEMICOLON = ';'
IF = 'if'
LET = 'letrec'
LETREC = 'let'


class Ops(Enum):
    Add = '+'
    Sub = '-'
    Mul = '*'
    Eq = '='
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
    If = IF
    Let = LET


class Token(namedtuple('Token', ['type', 'value'])):
    def __str__(self):
        return 'Token(type={}, value={})'.format(self.type, self.value)

class Lexer:
    '''
    Taken from https://eli.thegreenplace.net/2013/06/25/regex-based-lexical-analysis-in-python-and-javascript/
    '''
    class Error(Exception):
        pass

    def __init__(self, rules):
        regex_clauses = []
        self.converters = {}
        self.type_map = {}
        for idx, (regex, type, converter) in enumerate(rules):
            group_name = 'GROUP{}'.format(idx)
            regex_clauses.append('(?P<{}>{})'.format(group_name, regex))
            self.type_map[group_name] = type
            self.converters[group_name] = converter

        self.regex = re.compile('|'.join(regex_clauses))
        self.skip_whitespace_regex = re.compile('\S')

    def tokens(self, buf):
        pos = 0
        while True:
            res = self.next_token(buf, pos)
            if res is None:
                break
            token, pos = res

            yield token

    def next_token(self, buf, pos):
        if pos >= len(buf):
            return None

        m = self.skip_whitespace_regex.search(buf, pos)

        if m:
            pos = m.start()
        else:
            return None

        m = self.regex.match(buf, pos)

        if m:
            group_name = m.lastgroup
            token_type = self.type_map[group_name]
            converter = self.converters[group_name]

            token = Token(token_type, converter(m.group(group_name)))
            pos = m.end()
            return token, pos

        raise self.Error(pos)


class TokenType:
    class Quote: pass
    class LParen: pass
    class RParen: pass
    class Int: pass
    class Keyword: pass
    class Op: pass
    class Var: pass
    class Bool: pass

def convert_to_bool(elt):
    if elt == '#t':
        return True
    if elt == '#f':
        return False

    raise ValueError
    
identity = lambda x: x

lisp_rules = [
    (IF, TokenType.Keyword, identity),
    ('lambda', TokenType.Keyword, identity),
    (LET, TokenType.Keyword, identity),
    (LETREC, TokenType.Keyword, identity),
    ('\'', TokenType.Quote, identity),
    ('\+', TokenType.Op, identity),
    ('\-', TokenType.Op, identity),
    ('\*', TokenType.Op, identity),
    ('=', TokenType.Op, identity),
    ('<=', TokenType.Op, identity),
    ('or', TokenType.Op, identity),
    ('and', TokenType.Op, identity),
    ('not', TokenType.Op, identity),
    ('cons', TokenType.Op, identity),
    ('car', TokenType.Op, identity),
    ('cdr', TokenType.Op, identity),
    ('null\?', TokenType.Op, identity),
    ('\(', TokenType.LParen, identity),
    ('\)', TokenType.RParen, identity),
    ('[-+]?[0-9]+', TokenType.Int, int),
    ('#t', TokenType.Bool, convert_to_bool),
    ('#f', TokenType.Bool, convert_to_bool),
    ('[a-zA-Z_0-9\!\-\?#]*', TokenType.Var, identity)
]

lisp_lexer = Lexer(lisp_rules)

SExp = namedtuple('SExp', ['operator', 'operands'])
LambdaExp = namedtuple('LambdaExp', ['arglist', 'body'])
IfExp = namedtuple('IfExp', ['cond', 'if_true', 'if_false'])
Binding = namedtuple('Binding', ['var', 'value'])
LetExp = namedtuple('LetExp', ['bindings', 'body'])
VarExp = namedtuple('VarExp', ['name'])

class Parser:
    class Tokenizer:
        def __init__(self, tokens):
            self.tokens = list(tokens)

        def top(self):
            return self.tokens[0]

        def pop(self):
            self.tokens.pop(0)

        def no_more_tokens(self):
            return len(self.tokens) == 0
    
    class Error(Exception):
        pass

    @classmethod
    def require(cls, cond, msg=None):
        if not cond:
            raise cls.Error(msg)

    @classmethod
    def parse(cls, text):
        tokenizer = cls.Tokenizer(lisp_lexer.tokens(text))
        return cls(tokenizer).parse_exp()

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def pop_lparen_or_die(self):
        self.require(self.tokenizer.top().type == TokenType.LParen)
        self.tokenizer.pop()

    def pop_rparen_or_die(self):
        self.require(self.tokenizer.top().type == TokenType.RParen)
        self.tokenizer.pop()

    @staticmethod
    def is_let(token):
        # I'm not handling all the different let, let*, letrecs properly
        # I think what I have is closes to letrec
        return token in (LET, LETREC)
        
    def parse_item(self):
        if self.tokenizer.top().type == TokenType.LParen:
            self.tokenizer.pop()

            top_token = self.tokenizer.top()
            top_token_type = top_token.type
            top_token_value = top_token.value
            
            if top_token_type == TokenType.Keyword and \
               top_token_value == LAMBDA:
                self.tokenizer.pop()
                res = self.parse_lambda()
            elif top_token_type == TokenType.Keyword and \
                 top_token_value == IF:
                self.tokenizer.pop()
                res = self.parse_if()
            elif top_token_type == TokenType.Keyword and \
                 self.is_let(top_token_value):
                self.tokenizer.pop()
                res = self.parse_let()
            else:
                res = self.parse_s_exp_body()
            self.pop_rparen_or_die()
        else:
            res = self.parse_atom()

        return res

    def parse_exp(self):
        res = self.parse_item()
        self.require(self.tokenizer.no_more_tokens())
        return res

    def parse_let(self):
        def parse_bindings():
            res = []
            while self.tokenizer.top().type == TokenType.LParen:
                self.tokenizer.pop()
                top = self.tokenizer.top()
                self.require(top.type == TokenType.Var, top)
                var = VarExp(top.value)
                self.tokenizer.pop()
                top = self.tokenizer.top()
                value = self.parse_item()
                self.pop_rparen_or_die()
                res.append(Binding(var=var, value=value))
            return res
        
        def parse_body():
            return self.parse_item()
        
        self.pop_lparen_or_die()
        bindings = parse_bindings()
        self.pop_rparen_or_die()
        
        body = parse_body()

        return LetExp(bindings=bindings, body=body)

    def parse_if(self):
        cond = self.parse_item()

        if_true = self.parse_item()

        if_false = self.parse_item()

        return IfExp(cond=cond,
                     if_true=if_true,
                     if_false=if_false)

    def parse_lambda(self):
        def parse_arglist():
            self.pop_lparen_or_die()
            res = []
            while self.tokenizer.top().type != TokenType.RParen:
                top = self.tokenizer.top()
                self.require(top.type == TokenType.Var, top)
                res.append(VarExp(top.value))
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

        if next_tok.type in (TokenType.Int, TokenType.Bool):
            self.tokenizer.pop()
            return next_tok.value
        elif next_tok.type ==  TokenType.Op:
            self.tokenizer.pop()
            return Ops(next_tok.value)
        elif next_tok.type == TokenType.Var:
            self.tokenizer.pop()
            return VarExp(name=next_tok.value)

        self.require(False, next_tok)

    def parse_s_exp_body(self):
        operator = self.parse_item()
        operands = []
        while self.tokenizer.top().type != TokenType.RParen:
            operands.append(self.parse_item())

        return SExp(operator=operator,
                    operands=operands)


class Lisp2Cpp:
    class ConvertError(Exception):
        pass

    header_name = 'tmp_lisp.hpp'
    
    include = '#include "{}"\n\r\n\r'.format(header_name)

    def __init__(self, text):
        self.parse = Parser.parse(text)
        self.varmap = {}
        self.compute_varmap(self.parse, self.varmap)

    @classmethod
    def compute_varmap(cls, parse, varmap):
        if isinstance(parse, SExp):
            cls.compute_varmap(parse.operator, varmap)
            for operand in parse.operands:
                cls.compute_varmap(operand, varmap)
        elif isinstance(parse, LambdaExp):
            for exp in parse.arglist:
                cls.compute_varmap(exp, varmap)
            cls.compute_varmap(parse.body, varmap)
        elif isinstance(parse, VarExp):
            if parse.name not in varmap:
                varmap[parse.name] = len(varmap)
        elif isinstance(parse, LetExp):
            for binding in parse.bindings:
                if binding.var.name not in varmap:
                    varmap[binding.var.name] = len(varmap)
                cls.compute_varmap(binding.value, varmap)
            cls.compute_varmap(parse.body, varmap)

    def codegen_varlist(self):
        res = ''
        for name, ix in self.varmap.items():
            res += 'using {name_alias} = Var<{ix}>;\n'.format(
                name_alias=self.codegen_var(name),
                ix=ix
            )
        return res + '\n'

    @classmethod
    def paste_header(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, cls.header_name), 'r') as f:
            res = '/******************* BEGIN TMP_LISP *************/' + \
                f.read() +  \
                '\n\r/********************** END TMP_LISP ***************/' + \
                '\n\r\n\r'
            res = res.replace('#pragma once', '')
            return res
    
    def codegen(self, evaluate=False, include_header=False):
        if include_header:
            res = self.paste_header()
        else:
            res = self.include
        res += self.codegen_varlist()
        res += 'using Result = Eval<{}, EmptyEnv>'.format(self.codegen_(self.parse)) + ';'

        if evaluate:
            res += '\n\rtypename Result::force_compiler_error eval;'

        return res

    def codegen_(self, parse):
        if isinstance(parse, LambdaExp):
            return 'Lambda<{body_codegen}, EmptyEnv, {params_codegen}>'.format(
                body_codegen=self.codegen_(parse.body),
                params_codegen=','.join(self.codegen_(param)
                                        for param in parse.arglist)
            )
        elif isinstance(parse, LetExp):
            return 'Let<{env_codegen}, {body_codegen}>'.format(
                env_codegen=self.env_codegen(parse.bindings),
                body_codegen=self.codegen_(parse.body))
        elif isinstance(parse, SExp):
            return 'SExp<{operator}, {operands_codegen}>'.format(
                operator=self.codegen_(parse.operator),
                operands_codegen=','.join(self.codegen_(operand)
                                          for operand in parse.operands)
            )
        elif isinstance(parse, IfExp):
            return 'If<{cond}, {if_true}, {if_false}>'.format(
                cond=self.codegen_(parse.cond),
                if_true=self.codegen_(parse.if_true),
                if_false=self.codegen_(parse.if_false)
            )
        elif isinstance(parse, bool):
            return 'Bool<{}>'.format(str(parse).lower())
        elif isinstance(parse, int):
            return 'Int<{}>'.format(parse)
        elif isinstance(parse, VarExp):
            return self.codegen_var(parse.name)
        elif isinstance(parse, Ops):
            return 'Op<OpCode::{}>'.format(parse.name)
        elif isinstance(parse, bool):
            return 'Bool<{}>'.format(parse)
        else:
            raise self.ConvertError(
                'don\'t know how to convert{} to CPP'.format(parse))

    @staticmethod
    def name_to_cpp(lisp_var_name):
        return re.sub('[^0-9a-zA-Z_]+', '_', lisp_var_name)
        
    def codegen_var(self, name):
        return 'Var_{}'.format(self.name_to_cpp(name))
        
    def env_codegen(self, bindings):
        return 'Env<{bindings_codegen}>'.format(
            bindings_codegen=','.join(
                'Binding<{var}, {value}>'.format(
                    var=self.codegen_(binding.var),
                    value=self.codegen_(binding.value)
                    ) for binding in bindings
                ))

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',
                        '-i',
                        help='pass lisp on the command line',
                        type=str,
                        default=None)
    parser.add_argument('--file',
                        '-f',
                        help='read lisp from file',
                        type=str,
                        default=None)
    parser.add_argument('--eval',
                        '-e',
                        help='evaluate the expression by asking for a non-existent member type alias',
                        action='store_true')
    parser.add_argument('--include-header',
                        help='instead of having and include line, paste the entire header include',
                        action='store_true')
    return parser
    
def main(args):
    lisp_str = ''
    if args.input:
        lisp_str = args.input
    elif args.file:
        with open(args.file, 'r') as f:
            lisp_str = f.read()

    if not lisp_str:
        return
            
    print(Lisp2Cpp(lisp_str).codegen(evaluate=args.eval,
                                     include_header=args.include_header))

if __name__ == '__main__':
    main(create_parser().parse_args())
