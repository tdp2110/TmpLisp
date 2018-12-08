import unittest

from lisp2cpp import *


class TokenizerTest(unittest.TestCase):
    def test_1(self):
        var0 = 'var0'
        var1 = 'var1'
        expr = '( * {var0}   {var1} ))'.format(var0=var0,
                                               var1=var1)

        tokens = Tokenizer(expr).tokens
        self.assertEqual(
            tokens,
            [LPAREN, Ops.Mul, Var(var0), Var(var1), RPAREN, RPAREN])

    def test_2(self):
        var0 = 'var0'
        expr = '( lambda (x) (+ x 1))'
        tokens = Tokenizer(expr).tokens
        x_var = Var('x')
        self.assertEqual(
            tokens,
            [LPAREN, Keywords.Lambda, LPAREN, x_var, RPAREN,
             LPAREN, Ops.Add, x_var, Int(1), RPAREN, RPAREN])

if __name__ == '__main__':
    unittest.main()
