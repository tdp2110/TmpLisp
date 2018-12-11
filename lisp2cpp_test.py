import unittest

from lisp2cpp import *


class TokenizerTest(unittest.TestCase):
    @staticmethod
    def tokenize(text):
        return list(lisp_lexer.tokens(text))
    
    def test_1(self):
        var0 = 'var0'
        var1 = 'var1'
        expr = '( * {var0}   {var1} ))'.format(var0=var0,
                                               var1=var1)

        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.LParen, TokenType.Op, TokenType.Var, TokenType.Var,
             TokenType.RParen, TokenType.RParen])

        self.assertEqual(
            [_.value for _ in tokens],
            [LPAREN, '*', var0, var1, RPAREN, RPAREN])

    def test_2(self):
        expr = '( lambda (x) (+ x 1))'
        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.LParen, TokenType.Keyword, TokenType.LParen,
             TokenType.Var, TokenType.RParen, TokenType.LParen,
             TokenType.Op, TokenType.Var, TokenType.Int, TokenType.RParen,
             TokenType.RParen])
        
        self.assertEqual(
            [_.value for _ in tokens],
            [LPAREN, LAMBDA, LPAREN, 'x', RPAREN, LPAREN, '+',
             'x', 1, RPAREN, RPAREN])
        
    def comments_1(self):
        expr = ')(x;y()'
        tokens = self.tokenize(expr)
        self.assertEqual(
            tokens,
            [RPAREN, LPAREN, Var('x')])
        
    def _comments_2(self):
        expr = ')(x;y()\n);omg'
        tokens = self.tokenize(expr)
        self.assertEqual(
            tokens,
            [RPAREN, LPAREN, Var('x'), RPAREN])
        
    def test_no_whitespace(self):
        expr = '(lambda(x)(+ x 1))'
        tokens = self.tokenize(expr)
        
        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.LParen, TokenType.Keyword, TokenType.LParen,
             TokenType.Var, TokenType.RParen, TokenType.LParen, TokenType.Op,
             TokenType.Var, TokenType.Int, TokenType.RParen, TokenType.RParen])

        self.assertEqual(
            [_.value for _ in tokens],
            [LPAREN, LAMBDA, LPAREN, 'x', RPAREN, LPAREN, '+', 'x', 1, RPAREN, RPAREN])
            
    def test_emptylist_1(self):
        expr = '\'()'

        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.Quote, TokenType.LParen, TokenType.RParen])

        self.assertEqual(
            [_.value for _ in tokens],
            [QUOTE, LPAREN, RPAREN])
        
    def test_emptylist_2(self):
        expr = '\'( )'

        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.Quote, TokenType.LParen, TokenType.RParen])

        self.assertEqual(
            [_.value for _ in tokens],
            [QUOTE, LPAREN, RPAREN])
        
    def test_emptylist_3(self):
        varname = 'var'
        expr = '\'({})'.format(varname)

        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.type for _ in tokens],
            [TokenType.Quote, TokenType.LParen, TokenType.Var, TokenType.RParen])

        self.assertEqual(
            [_.value for _ in tokens],
            [QUOTE, LPAREN, varname, RPAREN])

    def test_booleans(self):
        expr = '((#t)(#f)(42))'

        tokens = self.tokenize(expr)

        self.assertEqual(
            [_.value for _ in tokens],
            [LPAREN, LPAREN, True, RPAREN, LPAREN, False,
             RPAREN, LPAREN, 42, RPAREN, RPAREN])

class ParserTest(unittest.TestCase):
    @staticmethod
    def parse(text):
        return Parser.parse(text)
    
    def test_1(self):
        varname = 'var'
        expr = '(* {var} 1)'.format(var=varname)

        parse = self.parse(expr)

        self.assertIsInstance(parse, SExp)
        self.assertEqual(parse.operator, Ops.Mul)
        self.assertEqual(parse.operands,
                         [VarExp(varname), 1])

    def test_lambda(self):
        varname = 'x'
        expr = '(lambda ({varname}) (+ {varname} 1))'.format(varname=varname)

        parse = self.parse(expr)

        expectedBody = SExp(operator=Ops.Add,
                            operands=[VarExp(varname), 1])
        
        self.assertIsInstance(parse, LambdaExp)
        self.assertEqual(parse.arglist, [VarExp(varname)])
        self.assertEqual(parse.body, expectedBody)

class Lisp2CppTest(unittest.TestCase):
    @staticmethod
    def codegen(text):
        return Lisp2Cpp(text).codegen()
    
    def test_varmap_1(self):
        exp = '(lambda (x y) (+ x y z))'
        lisp2cpp = Lisp2Cpp(exp)

        self.assertEqual(set(lisp2cpp.varmap), {'x', 'y', 'z'})

    def test_codegen_1(self):
        exp = '(lambda (x y) (+ x 1 y))'

        self.codegen(exp)

    def test_codegen_2(self):
        exp = '(or #t #f #t)'

        assert False, self.codegen(exp)

    def test_codegen_3(self):
        exp = '(if #t 1 3)'

        assert False, self.codegen(exp)

    def test_codegen_4(self):
        exp = '(cons 0 (cons 1 (cons 2 3)))'

        assert False, self.codegen(exp)
        
if __name__ == '__main__':
    unittest.main()
