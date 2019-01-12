# TmpLisp
Attempt at implementing the Scheme dialect of Lisp in C++ Template Metaprogramming (work in progress).
I'm not the first person to attempt this.

_Requires C++17 and Python3_

## Introduction

A functional core of the Scheme Metacircular Evaluator turns out to be fairly easy to implement entirely in C++
template metaprogramming. This repo attempts to be such an implementation. Mutable state in scheme is not modeled,
nor are strings for the moment, as they cannot currently be easily used as template parameters, nor are considerably many language features (eg, `define` is not implemented, but `let` expressions are). Even among the implemented features,
adherence to the Scheme standard is not implied.

In this implementation, all Scheme values are represented by C++ types. For example, the integer 1 is represented by the type `Int<1>`. The `Eval` function is driven by template specialization, but implements the normal eval/apply dance present in any metacircular evaluator implementation.


Compile-time C++ has long been known to be Turing complete. Implementing Scheme, in particular the untyped Lambda Calculus, is a means of showing why this is the case.

## Examples

### Arithmetic

Consider the Scheme expression `(+ 1 2)`, which evaluates to 3. We can compile this into
a template metaprogram with

    python lisp2cpp.py -e -i '(+ 1 2)'

(*note*: Python 3 is required). This gives

    #include "tmp_lisp.hpp"

    using Result = Eval<SExp<Op<OpCode::Add>, Int<1>, Int<2>>, EmptyEnv>;

    typename Result::force_compiler_error eval;

Notice the straightforward mapping from the Scheme expression to a C++ template expression. Lisp expressions naturally turn into C++ types built out of primitives from tmp_lisp.hpp.
All lisp values are represented by C++ types.
The metafunction `Eval` computes an associated type of an expression, its value.

`force_compiler_error` is only present to produce a compiler error in which the compiler
will pretty print the (simplified) form of the type alias `Result`:

    $ clang++ add.cpp  -std=c++1z
    add.cpp:4:18: error: no type named 'force_compiler_error' in 'Int<3>'
    typename Result::force_compiler_error eval;
    ~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
    1 error generated.

The compiler error shows that `Result` is `Int<3>`.

### Factorial

Consider the Scheme program fact.scm:

    (letrec ((fact (lambda (n)
                  (if (= 0 n)
                      1
                      (* n (fact (- n 1)))))))
      (fact 10))

which computes the factorial of 10. We can compile this to a C++ template metaprogram using

    python lisp2cpp.py -f fact.scm -e

This writes a template metaprogram to the console, and passing through
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

Compiling, we get:

    ➜  TmpLisp git:(master) ✗ clang++ fact.cpp -std=c++1z
    fact.cpp:15:18: error: no type named 'force_compiler_error' in 'Int<3628800>'
    typename Result::force_compiler_error eval;
    ~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
    1 error generated.

One can indeed verify that 3628800 is the factorial of 10.

### mapcar

Consider mapcar.scm:

    (letrec ((fact (lambda (n)
                     (if (= 0 n)
                         1
                         (* n (fact (- n 1)))
                         )
                     ))               
             (mapcar (lambda (f list)
                       (if (null? list)
                           '()
                           (cons (f (car list))
                                 (mapcar f (cdr list)))
                           )))
             )
         (mapcar fact '(1 2 3 4 5)))

Which computes the factorial of each integer in 1..5. We compile this with `python lisp2cpp.py -e -f factorial.scm` and passing through `clang-format` we get

    #include "tmp_lisp.hpp"

    using Var_fact = Var<0>;
    using Var_n = Var<1>;
    using Var_mapcar = Var<2>;
    using Var_f = Var<3>;
    using Var_list = Var<4>;

    using Result = Eval<
        Let<Env<Binding<Var_fact,
                        Lambda<If<SExp<Op<OpCode::Eq>, Int<0>, Var_n>, Int<1>,
                                  SExp<Op<OpCode::Mul>, Var_n,
                                       SExp<Var_fact,
                                            SExp<Op<OpCode::Sub>, Var_n, Int<1>>>>>,
                               EmptyEnv, Var_n>>,
                Binding<Var_mapcar,
                        Lambda<If<SExp<Op<OpCode::IsNull>, Var_list>, EmptyList,
                                  SExp<Op<OpCode::Cons>,
                                       SExp<Var_f, SExp<Op<OpCode::Car>, Var_list>>,
                                       SExp<Var_mapcar, Var_f,
                                            SExp<Op<OpCode::Cdr>, Var_list>>>>,
                               EmptyEnv, Var_f, Var_list>>>,
            SExp<Var_mapcar, Var_fact,
                 Cons<Int<1>,
                      Cons<Int<2>,
                           Cons<Int<3>, Cons<Int<4>, Cons<Int<5>, EmptyList>>>>>>>,
        EmptyEnv>;
    typename Result::force_compiler_error eval;

Compiling we get:

    $ clang++ mapcar.cpp  -std=c++1z
    mapcar.cpp:28:18: error: no type named 'force_compiler_error' in 'Cons<Int<1>,
    Cons<Int<2>, Cons<Int<6>, Cons<Int<24>, Cons<Int<120>, EmptyList> > > > >'
    typename Result::force_compiler_error eval;
    ~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~~
    1 error generated.

