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
        var0 = 'var0'
        expr = '( lambda (x) (+ x 1))'
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
        
if __name__ == '__main__':
    unittest.main()
