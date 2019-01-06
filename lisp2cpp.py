
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
import os
import re


LPAREN = '('
RPAREN = ')'
QUOTE = '\''
LAMBDA = 'lambda'
SEMICOLON = ';'
IF = 'if'
LETREC = 'letrec'
LET = 'let'


class Token(namedtuple('Token', ['type', 'value'])):
    def __str__(self):
        return 'Token(type={}, value={})'.format(self.type, self.value)


class Lexer:
    '''
    Taken from https://eli.thegreenplace.net/2013/06/25/regex-based-lexical-analysis-in-python-and-javascript/
    '''
    class Error(Exception):
        pass

    def __init__(self, rules, comment_regex=None):
        regex_clauses = []
        self.converters = {}
        self.type_map = {}
        for idx, (regex, token_type) in enumerate(rules):
            group_name = 'GROUP{}'.format(idx)
            regex_clauses.append('(?P<{}>{})'.format(group_name, regex))
            self.type_map[group_name] = token_type

        self.regex = re.compile('|'.join(regex_clauses))

        self.skip_whitespace_regex = re.compile(r'\S')
        if comment_regex is not None:
            self.comment_regex = re.compile(comment_regex)

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
            token = Token(token_type, m.group(group_name))
            pos = m.end()
            return token, pos

        raise self.Error((pos, buf[pos:]))


class TokenType:
    class Quote:
        pass

    class LParen:
        pass

    class RParen:
        pass

    class Comment:
        pass

    class Identifier:
        pass


lisp_rules = [
    (r'\'', TokenType.Quote),
    (r'\(', TokenType.LParen),
    (r'\)', TokenType.RParen),
    (r'[a-zA-Z_0-9\!\-\+\*\?#=<>]+', TokenType.Identifier),
    (r';[^\n\r]*(?:$|\n|\r)', TokenType.Comment)
]

lisp_lexer = Lexer(lisp_rules)

SExp = namedtuple('SExp', ['operator', 'operands'])
LambdaExp = namedtuple('LambdaExp', ['arglist', 'body'])
IfExp = namedtuple('IfExp', ['cond', 'if_true', 'if_false'])
Binding = namedtuple('Binding', ['var', 'value'])
LetExp = namedtuple('LetExp', ['bindings', 'body'])
VarExp = namedtuple('VarExp', ['name'])
ListExp = namedtuple('ListExp', ['values'])
OpExp = namedtuple('OpExp', ['value'])


class Parser:
    class Tokenizer:
        def __init__(self, tokens):
            self.tokens = list(tokens)

        def top(self):
            return self.tokens[0]

        def pop(self):
            return self.tokens.pop(0)

        def no_more_tokens(self):
            return len(self.tokens) == 0

    class Error(Exception):
        pass

    ops = {'+': 'Add',
           '-': 'Sub',
           '*': 'Mul',
           '=': 'Eq',
           '<=': 'Leq',
           'or': 'Or',
           'and': 'And',
           'not': 'Not',
           'cons': 'Cons',
           'car': 'Car',
           'cdr': 'Cdr',
           'null?': 'IsNull'}

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
        self.integer_regex = re.compile(r'^[-+]?[0-9]+$')

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
        while self.tokenizer.top() == TokenType.Comment:
            self.tokenizer.pop()

        top_token = self.tokenizer.top()
        top_token_type = top_token.type

        if top_token_type == TokenType.LParen:
            self.tokenizer.pop()
            res = self.parse_s_exp()
            self.pop_rparen_or_die()
        elif top_token_type == TokenType.Identifier:
            res = self.parse_identifier()
        else:
            res = self.parse_atom()

        return res

    def parse_identifier(self):
        tok = self.tokenizer.pop()
        assert tok.type == TokenType.Identifier, tok
        identifier = tok.value

        if identifier in self.ops:
            return OpExp(self.ops[identifier])
        elif identifier == '#t':
            return True
        elif identifier == '#f':
            return False
        elif re.match(self.integer_regex, identifier):
            return int(identifier)
        else:
            return VarExp(identifier)

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
                self.require(top.type == TokenType.Identifier, top)
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
                param = self.parse_item()
                self.require(isinstance(param, VarExp), top)
                res.append(param)
            self.tokenizer.pop()
            return res

        def parse_body():
            return self.parse_item()

        return LambdaExp(
            arglist=parse_arglist(),
            body=parse_body())

    def parse_atom(self):
        next_tok = self.tokenizer.top()
        if next_tok.type == TokenType.Identifier:
            return self.parse_identifier()
        elif next_tok.type == TokenType.Quote:
            self.tokenizer.pop()
            return self.parse_quoted_list()

        self.require(False, next_tok)

    def parse_quoted_list(self):
        self.pop_lparen_or_die()
        values = []
        while self.tokenizer.top().type != TokenType.RParen:
            item = self.parse_atom()
            if isinstance(item, VarExp):
                raise self.Error('don\'t know how to handle strings yet')
            values.append(item)
        self.pop_rparen_or_die()
        return ListExp(values=values)

    def parse_s_exp(self):
        tok = self.tokenizer.top()
        if tok.type == TokenType.Identifier:
            identifier = tok.value
            if identifier == IF:
                self.tokenizer.pop()
                return self.parse_if()
            elif identifier == LAMBDA:
                self.tokenizer.pop()
                return self.parse_lambda()
            elif self.is_let(identifier):
                self.tokenizer.pop()
                return self.parse_let()

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
            res = res.replace('#pragma once', '')  # such a hack ...
            return res

    def codegen(self, evaluate=False, include_header=False):
        if include_header:
            res = self.paste_header()
        else:
            res = self.include
        res += self.codegen_varlist()
        res += 'using Result = Eval<{}, EmptyEnv>'.format(
            self.codegen_(self.parse)) + ';'

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
        elif isinstance(parse, OpExp):
            return 'Op<OpCode::{}>'.format(parse.value)
        elif isinstance(parse, bool):
            return 'Bool<{}>'.format(parse)
        elif isinstance(parse, ListExp):
            return self.codegen_list(parse.values)
        else:
            raise self.ConvertError(
                'don\'t know how to convert {} to CPP'.format(parse))

    @staticmethod
    def name_to_cpp(lisp_var_name):
        return re.sub('[^0-9a-zA-Z_]+', '_', lisp_var_name)

    def codegen_list(self, list_values):
        if not list_values:
            return 'EmptyList'
        return 'Cons<{}, {}>'.format(self.codegen_(list_values[0]),
                                     self.codegen_list(list_values[1:]))

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
