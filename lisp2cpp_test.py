from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory
import unittest

from pathlib import Path

from lisp2cpp import (
    TokenType,
    lisp_lexer,
    QUOTE,
    LPAREN,
    LAMBDA,
    RPAREN,
    Parser,
    Lisp2Cpp,
    SExp,
    VarExp,
    OpExp,
    LambdaExp,
)


class TokenizerTest(unittest.TestCase):
    @staticmethod
    def tokenize(text):
        return list(lisp_lexer.tokens(text))

    @staticmethod
    def token_types(tokens):
        return [_.type for _ in tokens]

    @staticmethod
    def token_values(tokens):
        return [_.value for _ in tokens]

    def test_1(self):
        var0 = "var0"
        var1 = "var1"
        var2 = "123abc"
        expr = "( * {var0}   {var1} {var2}))".format(var0=var0, var1=var1, var2=var2)

        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.RParen,
                TokenType.RParen,
            ],
        )

        self.assertEqual(
            self.token_values(tokens), [LPAREN, "*", var0, var1, var2, RPAREN, RPAREN]
        )

    def test_2(self):
        expr = "( lambda (x) (+ x 1))"
        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.RParen,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.RParen,
                TokenType.RParen,
            ],
        )

        self.assertEqual(
            self.token_values(tokens),
            [
                LPAREN,
                LAMBDA,
                LPAREN,
                "x",
                RPAREN,
                LPAREN,
                "+",
                "x",
                "1",
                RPAREN,
                RPAREN,
            ],
        )

    def test_comments_1(self):
        expr = ")(x;y()\n"
        tokens = self.tokenize(expr)
        self.assertEqual(
            self.token_types(tokens),
            [
                TokenType.RParen,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.Comment,
            ],
        )

    def test_comments_2(self):
        expr = ")(x;y()\n  );omg"
        tokens = self.tokenize(expr)
        self.assertEqual(
            self.token_types(tokens),
            [
                TokenType.RParen,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.Comment,
                TokenType.RParen,
                TokenType.Comment,
            ],
        )

    def test_no_whitespace(self):
        expr = "(lambda(x)(+ x 1))"
        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.RParen,
                TokenType.LParen,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.Identifier,
                TokenType.RParen,
                TokenType.RParen,
            ],
        )

        self.assertEqual(
            self.token_values(tokens),
            [
                LPAREN,
                LAMBDA,
                LPAREN,
                "x",
                RPAREN,
                LPAREN,
                "+",
                "x",
                "1",
                RPAREN,
                RPAREN,
            ],
        )

    def test_emptylist_1(self):
        expr = "'()"

        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [TokenType.Quote, TokenType.LParen, TokenType.RParen],
        )

        self.assertEqual(self.token_values(tokens), [QUOTE, LPAREN, RPAREN])

    def test_emptylist_2(self):
        expr = "'( )"

        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [TokenType.Quote, TokenType.LParen, TokenType.RParen],
        )

        self.assertEqual(self.token_values(tokens), [QUOTE, LPAREN, RPAREN])

    def test_emptylist_3(self):
        varname = "var"
        expr = "'({})".format(varname)

        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_types(tokens),
            [TokenType.Quote, TokenType.LParen, TokenType.Identifier, TokenType.RParen],
        )

        self.assertEqual(self.token_values(tokens), [QUOTE, LPAREN, varname, RPAREN])

    def test_booleans(self):
        expr = "((#t)(#f)(42))"

        tokens = self.tokenize(expr)

        self.assertEqual(
            self.token_values(tokens),
            [
                LPAREN,
                LPAREN,
                "#t",
                RPAREN,
                LPAREN,
                "#f",
                RPAREN,
                LPAREN,
                "42",
                RPAREN,
                RPAREN,
            ],
        )


class ParserTest(unittest.TestCase):
    @staticmethod
    def parse(text):
        return Parser.parse(text)

    def test_1(self):
        varname = "var"
        expr = "(* {var} 1)".format(var=varname)

        parse = self.parse(expr)

        self.assertIsInstance(parse, SExp)
        self.assertEqual(parse.operator.value, Parser.ops["*"])
        self.assertEqual(parse.operands, [VarExp(varname), 1])

    def test_lambda(self):
        varname = "x"
        expr = "(lambda ({varname}) (+ {varname} 1))".format(varname=varname)

        parse = self.parse(expr)
        expectedBody = SExp(operator=OpExp("Add"), operands=[VarExp(varname), 1])

        self.assertIsInstance(parse, LambdaExp)
        self.assertEqual(parse.arglist, [VarExp(varname)])
        self.assertEqual(parse.body, expectedBody)


class Lisp2CppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = TemporaryDirectory()
        cls.temp_dir_name = Path(cls.temp_dir.name)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    @staticmethod
    def codegen(text):
        return Lisp2Cpp(text).codegen()

    @property
    def compiler_outfile(self):
        return self.temp_dir_name / "a.out"

    def check_cppeval(self, lisp_code, expected_result):
        cpp_code = "#include <type_traits>\n\r\n\r"
        cpp_code += Lisp2Cpp(lisp_code).codegen(evaluate=False, include_header=True)
        cpp_code += "\n\r\n\r"
        cpp_code += "static_assert(std::is_same<Result, {}>::value);".format(
            expected_result
        )

        self.check_compiles(cpp_code)

    def check_compiles(self, code):
        with Popen(["echo", code], stdout=PIPE) as codegen_process, Popen(
            ["c++", "-xc++", "-std=c++1z", "-", "-c", "-o", self.compiler_outfile],
            stdin=codegen_process.stdout,
            stdout=PIPE,
        ) as compile_process:
            out, err = compile_process.communicate()

        self.assertEqual(compile_process.returncode, 0, (out, err))

    def test_varmap_1(self):
        exp = "(lambda (x y) (+ x y z))"
        lisp2cpp = Lisp2Cpp(exp)

        self.assertEqual(set(lisp2cpp.varmap), {"x", "y", "z"})

    def test_compile_subprocess(self):
        self.check_compiles("int main(){}")

        with self.assertRaises(AssertionError):
            self.check_compiles("int main(){")

    def test_codegen_1(self):
        self.check_cppeval("(+ 2 3)", "Int<5>")

    def test_codegen_2(self):
        exp = "((lambda (x y) (+ x 1 y)) 2 3)"

        self.check_cppeval(exp, "Int<6>")

    def test_codegen_3(self):
        exp = "(or #t #f #t)"

        self.check_cppeval(exp, "True")

    def test_codegen_4(self):
        exp = "(if #t 1 3)"

        self.check_cppeval(exp, "Int<1>")

    def test_codegen_5(self):
        list_exp = "(cons 0 (cons 1 (cons 2 3)))"
        exp = "(car (cdr (cdr {})))".format(list_exp)

        self.check_cppeval(exp, "Int<2>")

    def test_let(self):
        exp = "(let ((x 1)(y 2)) (+ x y))"

        self.check_cppeval(exp, "Int<3>")

    def test_factorial(self):
        def fact(n):
            if n == 0:
                return 1
            return n * fact(n - 1)

        for integer in [0, 1, 10]:
            exp = """(letrec ((fact (lambda (n)
                                  (if (= 0 n)
                                      1
                                      (* n (fact (- n 1)))))))
                       (fact {}))""".format(
                integer
            )

            self.check_cppeval(exp, "Int<{}>".format(fact(integer)))

    def test_mapcar(self):
        def mapcar_exp(func_exp, list_exp):
            return """(letrec ((mapcar (lambda (func list)
                                       (if (null? list)
                                           '()
                                           (cons (func (car list)) (mapcar func (cdr list)))
                                        ))))
                        (mapcar {func_exp} {list_exp}))""".format(
                func_exp=func_exp, list_exp=list_exp
            )

        list_exp = "'(1 2 3)"
        double_fun = "(lambda (arg) (* arg 2))"

        self.check_cppeval(
            mapcar_exp(func_exp=double_fun, list_exp=list_exp),
            "Cons<Int<2>, Cons<Int<4>, Cons<Int<6>, EmptyList>>>",
        )

    def test_mess_with_keywords(self):
        exp = """(let ((if 1)
                       (lambda_var 1)
                       (++ 1)
                       (and_exp 1)
                       (123abc 1) )
                     (+ if lambda_var and_exp ++ 123abc))"""

        self.check_cppeval(exp, "Int<5>")

    def test_fib(self):
        def fib_exp(n):
            return """(letrec ((fib (lambda (n)
                                      (if (<= n 0)
                                          1
                                          (+ (fib (- n 1)) (fib (- n 2)))))))
                         (fib {}))""".format(
                n
            )

        def fib_py(n):
            if n <= 0:
                return 1
            return fib_py(n - 1) + fib_py(n - 2)

        for n in range(10):
            self.check_cppeval(fib_exp(n), "Int<{}>".format(fib_py(n)))

    def test_unary_minus(self):
        self.check_cppeval("(- 1)", "Int<-1>")
        self.check_cppeval("(- 0)", "Int<0>")

    def test_lots_of_minuses(self):
        self.check_cppeval("(- 1 2)", "Int<-1>")
        self.check_cppeval("(- 1 2 3)", "Int<-4>")


if __name__ == "__main__":
    unittest.main()
