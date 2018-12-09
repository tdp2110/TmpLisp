import unittest

from lisp2cpp import *


class TokenizerTest(unittest.TestCase):
    @staticmethod
    def tokenize(text):
        return Tokenizer(text).tokens
    
    def test_1(self):
        var0 = 'var0'
        var1 = 'var1'
        expr = '( * {var0}   {var1} ))'.format(var0=var0,
                                               var1=var1)

        tokens = self.tokenize(expr)
        self.assertEqual(
            tokens,
            [LPAREN, Ops.Mul, Var(var0), Var(var1), RPAREN, RPAREN])

    def test_2(self):
        expr = '( lambda (x) (+ x 1))'
        tokens = self.tokenize(expr)
        x_var = Var('x')
        self.assertEqual(
            tokens,
            [LPAREN, Keywords.Lambda, LPAREN, x_var, RPAREN,
             LPAREN, Ops.Add, x_var, Int(1), RPAREN, RPAREN])

    def test_comments_1(self):
        expr = ')(x;y()'
        tokens = self.tokenize(expr)
        self.assertEqual(
            tokens,
            [RPAREN, LPAREN, Var('x')])
        
    def test_comments_2(self):
        expr = ')(x;y()\n);omg'
        tokens = self.tokenize(expr)
        self.assertEqual(
            tokens,
            [RPAREN, LPAREN, Var('x'), RPAREN])
        
    def test_no_whitespace(self):
        expr = '(lambda(x)(+ x 1))'
        tokens = self.tokenize(expr)
        x_var = Var('x')
        self.assertEqual(
            tokens,
            [LPAREN, Keywords.Lambda, LPAREN, x_var, RPAREN,
             LPAREN, Ops.Add, x_var, Int(1), RPAREN, RPAREN])

    def test_emptylist_1(self):
        expr = '\'()'
        self.assertEqual(
            self.tokenize(expr),
            [QUOTE_LPAREN, RPAREN])
        
    def test_emptylist_2(self):
        expr = '\'( )'

        self.assertEqual(
            self.tokenize(expr),
            [QUOTE_LPAREN, RPAREN])
        
    def test_emptylist_3(self):
        varname = 'var'
        expr = '\'({})'.format(varname)

        self.assertEqual(
            self.tokenize(expr),
            [QUOTE_LPAREN, Var(varname), RPAREN])

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
                         [Var(varname), Int(1)])

    def test_lambda(self):
        varname = 'x'
        expr = '(lambda ({varname}) (+ {varname} 1))'.format(varname=varname)

        parse = self.parse(expr)

        expectedBody = SExp(operator=Ops.Add,
                            operands=[Var(varname), Int(1)])
        
        self.assertIsInstance(parse, LambdaExp)
        self.assertEqual(parse.arglist, [Var(varname)])
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
        
if __name__ == '__main__':
    unittest.main()
