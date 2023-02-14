#  Restricted Scheme-like Language using Template Metaprogramming
#
#  Copyright Thomas D Peters 2018-present
#
#  Use, modification and distribution is subject to the
#  Boost Software License, Version 1.0. (See accompanying
#  file LICENSE or copy at
#  http://www.boost.org/LICENSE_1_0.txt)

import argparse
import enum
import os
import re
from collections import namedtuple

LPAREN = "("
RPAREN = ")"
QUOTE = "'"
LAMBDA = "lambda"
SEMICOLON = ";"
IF = "if"
LETREC = "letrec"
LET = "let"


Token = namedtuple("Token", ["type", "value"])


class Lexer:
    """
    Approach taken from https://eli.thegreenplace.net/2013/06/25/regex-based-lexical-analysis-in-python-and-javascript/
    """

    class Error(Exception):
        pass

    def __init__(self, rules, comment_regex=None):
        regex_clauses = []
        self.type_map = {}
        for idx, (regex, token_type) in enumerate(rules):
            group_name = f"GROUP{idx}"
            regex_clauses.append(f"(?P<{group_name}>{regex})")
            self.type_map[group_name] = token_type

        self.regex = re.compile("|".join(regex_clauses))

        self.skip_whitespace_regex = re.compile(r"\S")
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


class TokenType(enum.Enum):
    Quote = enum.auto()
    LParen = enum.auto()
    RParen = enum.auto()
    Comment = enum.auto()
    Identifier = enum.auto()


lisp_rules = [
    (r"\'", TokenType.Quote),
    (r"\(", TokenType.LParen),
    (r"\)", TokenType.RParen),
    (r"[a-zA-Z_0-9\!\-\+\*\?#=<>]+", TokenType.Identifier),
    (r";[^\n\r]*(?:$|\n|\r)", TokenType.Comment),
]

lisp_lexer = Lexer(lisp_rules)

SExp = namedtuple("SExp", ["operator", "operands"])
LambdaExp = namedtuple("LambdaExp", ["arglist", "body"])
IfExp = namedtuple("IfExp", ["cond", "if_true", "if_false"])
Binding = namedtuple("Binding", ["var", "value"])
LetExp = namedtuple("LetExp", ["bindings", "body"])
VarExp = namedtuple("VarExp", ["name"])
ListExp = namedtuple("ListExp", ["values"])
OpExp = namedtuple("OpExp", ["value"])


class Parser:
    class Tokenizer:
        def __init__(self, text):
            self.tokens = list(lisp_lexer.tokens(text))

        def top(self):
            return self.tokens[0]

        def pop(self):
            return self.tokens.pop(0)

        def no_more_tokens(self):
            return len(self.tokens) == 0

    class Error(Exception):
        pass

    ops = {
        "+": "Add",
        "-": "Sub",
        "*": "Mul",
        "=": "Eq",
        "<=": "Leq",
        "or": "Or",
        "and": "And",
        "not": "Not",
        "cons": "Cons",
        "car": "Car",
        "cdr": "Cdr",
        "null?": "IsNull",
    }

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.integer_regex = re.compile(r"^[-+]?[0-9]+$")

    @classmethod
    def parse(cls, text):
        tokenizer = cls.Tokenizer(text)
        return cls(tokenizer).parse_exp()

    def parse_exp(self):
        res = self._parse_item()
        self._require(self.tokenizer.no_more_tokens())
        return res

    def _pop_lparen_or_die(self):
        self._require(self.tokenizer.top().type == TokenType.LParen)
        self.tokenizer.pop()

    def _pop_rparen_or_die(self):
        self._require(self.tokenizer.top().type == TokenType.RParen)
        self.tokenizer.pop()

    @classmethod
    def _require(cls, cond, msg=None):
        if not cond:
            raise cls.Error(msg)

    @staticmethod
    def _is_let(token):
        # I'm not handling all the different let, let*, letrecs properly
        # I think what I have is closes to letrec
        return token in (LET, LETREC)

    def _parse_item(self):
        while self.tokenizer.top() == TokenType.Comment:
            self.tokenizer.pop()

        top_token = self.tokenizer.top()
        top_token_type = top_token.type

        if top_token_type == TokenType.LParen:
            self.tokenizer.pop()
            res = self._parse_parenthesized_exp()
            self._pop_rparen_or_die()
        elif top_token_type == TokenType.Identifier:
            res = self._parse_identifier()
        else:
            res = self._parse_atom()

        return res

    def _parse_identifier(self):
        tok = self.tokenizer.pop()
        assert tok.type == TokenType.Identifier, tok
        identifier = tok.value

        if identifier in self.ops:
            return OpExp(self.ops[identifier])
        if identifier == "#t":
            return True
        if identifier == "#f":
            return False
        if re.match(self.integer_regex, identifier):
            return int(identifier)
        return VarExp(identifier)

    def _var_exp(self, value):
        self._require(self.integer_regex.match(value) is None)
        return VarExp(value)

    def _parse_let(self):
        def parse_bindings():
            res = []
            while self.tokenizer.top().type == TokenType.LParen:
                self.tokenizer.pop()
                top = self.tokenizer.top()
                self._require(top.type == TokenType.Identifier, top)
                var = self._var_exp(top.value)
                self.tokenizer.pop()
                top = self.tokenizer.top()
                value = self._parse_item()
                self._pop_rparen_or_die()
                res.append(Binding(var=var, value=value))
            return res

        def parse_body():
            return self._parse_item()

        self._pop_lparen_or_die()
        bindings = parse_bindings()
        self._pop_rparen_or_die()

        body = parse_body()

        return LetExp(bindings=bindings, body=body)

    def _parse_if(self):
        cond = self._parse_item()

        if_true = self._parse_item()

        if_false = self._parse_item()

        return IfExp(cond=cond, if_true=if_true, if_false=if_false)

    def _parse_lambda(self):
        def parse_arglist():
            self._pop_lparen_or_die()
            res = []
            while self.tokenizer.top().type != TokenType.RParen:
                top = self.tokenizer.top()
                param = self._parse_item()
                self._require(isinstance(param, VarExp), top)
                res.append(param)
            self.tokenizer.pop()
            return res

        def parse_body():
            return self._parse_item()

        return LambdaExp(arglist=parse_arglist(), body=parse_body())

    def _parse_atom(self):
        next_tok = self.tokenizer.top()
        if next_tok.type == TokenType.Identifier:
            return self._parse_identifier()
        if next_tok.type == TokenType.Quote:
            self.tokenizer.pop()
            self._require(
                self.tokenizer.top().type == TokenType.LParen,
                "only know how to parse quoted lists right now",
            )
            return self._parse_quoted_list()

        self._require(False, next_tok)

    def _parse_quoted_list(self):
        self._pop_lparen_or_die()
        values = []
        while self.tokenizer.top().type != TokenType.RParen:
            item = self._parse_atom()
            if isinstance(item, VarExp):
                raise self.Error("don't know how to handle strings yet")
            values.append(item)
        self._pop_rparen_or_die()
        return ListExp(values=values)

    def _parse_parenthesized_exp(self):
        tok = self.tokenizer.top()
        if tok.type == TokenType.Identifier:
            identifier = tok.value
            if identifier == IF:
                self.tokenizer.pop()
                return self._parse_if()
            if identifier == LAMBDA:
                self.tokenizer.pop()
                return self._parse_lambda()
            if self._is_let(identifier):
                self.tokenizer.pop()
                return self._parse_let()

        operator = self._parse_item()
        operands = []
        while self.tokenizer.top().type != TokenType.RParen:
            operands.append(self._parse_item())

        return SExp(operator=operator, operands=operands)


class Lisp2Cpp:
    class ConvertError(Exception):
        pass

    header_name = "tmp_lisp.hpp"

    include = f'#include "{header_name}"\n\r\n\r'

    def __init__(self, text):
        self.parse = Parser.parse(text)
        self.varmap = {}
        self._compute_varmap(self.parse, self.varmap)

    def codegen(self, evaluate=False, include_header=False):
        if include_header:
            res = self._paste_header()
        else:
            res = self.include

        res += self._codegen_varlist()
        to_eval = self._codegen(self.parse)
        res += f"using Result = Eval<{to_eval}, EmptyEnv>;"

        if evaluate:
            res += "\n\nResult::force_compiler_error eval;"

        return res

    @classmethod
    def _compute_varmap(cls, parse, varmap):
        if isinstance(parse, SExp):
            cls._compute_varmap(parse.operator, varmap)
            for operand in parse.operands:
                cls._compute_varmap(operand, varmap)
        elif isinstance(parse, LambdaExp):
            for exp in parse.arglist:
                cls._compute_varmap(exp, varmap)
            cls._compute_varmap(parse.body, varmap)
        elif isinstance(parse, VarExp):
            if parse.name not in varmap:
                varmap[parse.name] = len(varmap)
        elif isinstance(parse, LetExp):
            for binding in parse.bindings:
                if binding.var.name not in varmap:
                    varmap[binding.var.name] = len(varmap)
                cls._compute_varmap(binding.value, varmap)
            cls._compute_varmap(parse.body, varmap)

    def _codegen_varlist(self):
        return "\n".join(
            f"using {self._codegen_var(name)} = Var<{ix}>;"
            for name, ix in self.varmap.items()
        )

    @classmethod
    def _paste_header(cls):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, cls.header_name), "r") as f:
            res = (
                "/******************* BEGIN TMP_LISP *************/"
                + f.read()
                + "\n\r/********************** END TMP_LISP ***************/"
                + "\n\r\n\r"
            )
            res = res.replace("#pragma once", "")  # such a hack ...
            return res

    def _codegen(self, parse):
        if isinstance(parse, LambdaExp):
            body_codegen = self._codegen(parse.body)
            params_codegen = ",".join(self._codegen(param) for param in parse.arglist)
            return f"Lambda<{body_codegen}, {params_codegen}>"
        if isinstance(parse, LetExp):
            env_codegen = self._env_codegen(parse.bindings)
            body_codegen = self._codegen(parse.body)
            return f"Let<{env_codegen}, {body_codegen}>"
        if isinstance(parse, SExp):
            operator = self._codegen(parse.operator)
            operands_codegen = ",".join(
                self._codegen(operand) for operand in parse.operands
            )
            return f"SExp<{operator}, {operands_codegen}>"
        if isinstance(parse, IfExp):
            cond = self._codegen(parse.cond)
            if_true = self._codegen(parse.if_true)
            if_false = self._codegen(parse.if_false)
            return f"If<{cond}, {if_true}, {if_false}>"
        if isinstance(parse, bool):
            return f"Bool<{str(parse).lower()}>"
        if isinstance(parse, int):
            return f"Int<{parse}>"
        if isinstance(parse, VarExp):
            return self._codegen_var(parse.name)
        if isinstance(parse, OpExp):
            return f"Op<OpCode::{parse.value}>"
        if isinstance(parse, ListExp):
            return self._codegen_list(parse.values)
        raise self.ConvertError(f"don't know how to convert {parse} to CPP")

    @staticmethod
    def name_to_cpp(lisp_var_name):
        return re.sub(r"[^0-9a-zA-Z_\-!\?#]+", "_", lisp_var_name)

    def _codegen_list(self, list_values):
        if not list_values:
            return "EmptyList"
        head = self._codegen(list_values[0])
        tail = self._codegen_list(list_values[1:])
        return f"Cons<{head}, {tail}>"

    def _codegen_var(self, name):
        return f"Var_{self.name_to_cpp(name)}"

    def _env_codegen(self, bindings):
        bindings_codegen = ",".join(
            f"Binding<{self._codegen(binding.var)}, {self._codegen(binding.value)}>".format()
            for binding in bindings
        )
        return f"Env<{bindings_codegen}>"


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", "-i", help="pass lisp on the command line", type=str, default=None
    )
    parser.add_argument(
        "--file", "-f", help="read lisp from file", type=str, default=None
    )
    parser.add_argument(
        "--eval",
        "-e",
        help="evaluate the expression by asking for a non-existent member type alias",
        action="store_true",
    )
    parser.add_argument(
        "--include-header",
        help="instead of having and include line, paste the entire header include",
        action="store_true",
    )
    return parser


def main(args):
    lisp_str = ""
    if args.input:
        lisp_str = args.input
    elif args.file:
        with open(args.file, "r") as f:
            lisp_str = f.read()

    if not lisp_str:
        return

    print(
        Lisp2Cpp(lisp_str).codegen(
            evaluate=args.eval, include_header=args.include_header
        )
    )


if __name__ == "__main__":
    main(create_parser().parse_args())
