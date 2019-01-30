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
