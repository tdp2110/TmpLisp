from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory
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
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
    
    @staticmethod
    def codegen(text):
        return Lisp2Cpp(text).codegen()

    @property
    def compiler_outfile(self):
        return os.path.join(self.temp_dir.name, 'a.out')
    
    def check_cppeval(self, lisp_code, expected_result):
        cpp_code = '#include <type_traits>\n\r\n\r'
        cpp_code += Lisp2Cpp(lisp_code).codegen(evaluate=False,
                                               include_header=True)
        cpp_code += '\n\r\n\r'
        cpp_code += 'static_assert(std::is_same<Result, {}>::value);'.format(expected_result)

        self.check_compiles(cpp_code)
    
    def check_compiles(self, code):
        codegen_process = Popen(['echo', code], stdout=PIPE)
        compile_process = Popen(['c++', '-xc++', '-std=c++1z', '-', '-c', '-o', self.compiler_outfile],
                                stdin=codegen_process.stdout,
                                stdout=PIPE)
        codegen_process.stdout.close()
        out, err = compile_process.communicate()

        self.assertEqual(compile_process.returncode, 0, (out, err))
    
    def test_varmap_1(self):
        exp = '(lambda (x y) (+ x y z))'
        lisp2cpp = Lisp2Cpp(exp)

        self.assertEqual(set(lisp2cpp.varmap), {'x', 'y', 'z'})

    def test_compile_subprocess(self):
        self.check_compiles('int main(){}')

        with self.assertRaises(AssertionError):
            self.check_compiles('int main(){')
    
    def test_codegen_1(self):
        self.check_cppeval('(+ 2 3)', 'Int<5>')
            
    def test_codegen_2(self):
        exp = '((lambda (x y) (+ x 1 y)) 2 3)'

        self.check_cppeval(exp, 'Int<6>')

    def test_codegen_3(self):
        exp = '(or #t #f #t)'

        self.check_cppeval(exp, 'True')
        
    def test_codegen_4(self):
        exp = '(if #t 1 3)'

        self.check_cppeval(exp, 'Int<1>')
        
    def test_codegen_5(self):
        list_exp = '(cons 0 (cons 1 (cons 2 3)))'
        exp = '(car (cdr (cdr {})))'.format(list_exp)

        self.check_cppeval(exp, 'Int<2>')
        
    def test_let(self):
        exp = '(let ((x 1)(y 2)) (+ x y))'

        self.check_cppeval(exp, 'Int<3>')

    def test_factorial(self):
        exp = '''(letrec ((fact (lambda (n)
                              (if (= 0 n)
                                  1
                                  (* n (fact (- n 1)))))))
                   (fact 10))'''

        def fact(n):
            if n == 0:
                return 1
            return n * fact(n - 1)
        
        self.check_cppeval(exp, 'Int<{}>'.format(fact(10)))
        
if __name__ == '__main__':
    unittest.main()
