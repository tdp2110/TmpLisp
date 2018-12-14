# TmpLisp
Attempt at implementing the Scheme dialect of Lisp in C++ Template Metaprogramming (work in progress).
I'm not the first person to attempt this.

_Requires C++17_

## Introduction

A functional core of the Scheme Metacircular Evaluator turns out to be fairly easy to implement entirely in C++
template metaprogramming. This repo attempts to be such an implementation. Mutable state in scheme is not modeled,
nor are strings for the moment, as they cannot currently be easily used as template parameters, nor are considerably many language features (eg, `define` is not implemented, but `let` expressions are). Even among the implemented features,
adherence to the Scheme standard is not implied.

Compile-time C++ has long been known to be Turing complete. Implementing Scheme, in particular the untyped Lambda Calculus, is a means of showing why this is the case.

## Examples

Consider the Scheme program fact.scm:

    (letrec ((fact (lambda (n)
                  (if (= 0 n)
                      1
                      (* n (fact (- n 1)))))))
      (fact 10))

which computes the factorial of 10. We can compile this to a C++ template metaprogram using

    python lisp2cpp.py -f fact.scm -e

(*note*: Python 3 is required). This writes a template metaprogram to the console, and passing through
clang-format we (currently) get:

    #include "tmp_lisp.hpp"

    using Var_fact = Var<0>;
    using Var_n = Var<1>;

    using Result =
        Eval<Let<Env<Binding<Var_fact,
                             Lambda<If<SExp<Op<OpCode::Eq>, Int<0>, Var_n>, Int<1>,
                                       SExp<Op<OpCode::Mul>, Var_n,
                                            SExp<Var_fact, SExp<Op<OpCode::Sub>,
                                                              Var_n, Int<1>>>>>,
                                    EmptyEnv, Var_n>>>,
                 SExp<Var_fact, Int<10>>>,
             EmptyEnv>;
    typename Result::force_compiler_error eval;

Lisp expressions naturally turn into C++ types built out of primitives from tmp_lisp.hpp.
All lisp values are represented by C++ types.
The metafunction `Eval` computes an associated type of an expression, its value.
The last line, `typename Result::force_compiler_error eval` is present only to
force a compiler error which should mention the type computed by `Eval`, `Result`.
For example, using clang we get the following output

    ➜  TmpLisp git:(master) ✗ clang++ fact.cpp -std=c++1z
    fact.cpp:15:18: error: no type named 'force_compiler_error' in 'Int<3628800>'
    typename Result::force_compiler_error eval;
    ~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
    1 error generated.

One can indeed verify that 3628800 is the factorial of 10.

`Eval` is driven by template specialization, but implements the normal eval/apply dance
present in any metacircular evaluator implementation.
