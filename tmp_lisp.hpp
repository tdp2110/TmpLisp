#pragma once

namespace TmpLisp {
  template<int i>
  struct IntConst {
    static constexpr int value = i;
  };

  template<int i>
  struct Var {};

  struct EmptyEnv {};
  
  template<class Exp, class Env>
  struct Eval;

  template<int i, class Env>
  struct Eval<IntConst<i>, Env>
  {
    using IntType = IntConst<i>;
    static constexpr int value = IntType::value;
  };
}
