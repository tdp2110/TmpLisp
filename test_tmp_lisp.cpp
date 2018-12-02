#include "tmp_lisp.hpp"

using namespace TmpLisp;

int main() {
  using Zero = IntConst<0>;
  using One = IntConst<1>;
  
  static_assert(Eval<Zero, EmptyEnv> == 0);
  static_assert(Eval<One, EmptyEnv> == 1);

  using Var0 = Var<0>;
  using Var1 = Var<1>;
  using Var2 = Var<2>;
  using MinusOne = IntConst<-1>;
  using MinusTwo = IntConst<-2>;
  using MinusThree = IntConst<-3>;
  using TestEnv1 = Env<Binding<Var0, MinusOne>,
                       Binding<Var1, MinusTwo>,
                       Binding<Var2, MinusThree>>;
  static_assert(Eval<Var0, TestEnv1> == MinusOne::value);
  static_assert(Eval<Var1, TestEnv1> == MinusTwo::value);
  static_assert(Eval<Var2, TestEnv1> == MinusThree::value);

  using TestIfExp1 = IfExp<Var0, Var1, Var2>;
  static_assert(Eval<TestIfExp1, TestEnv1> == Lookup<Var1, TestEnv1>);

  using TestIfExp2 = IfExp<Zero, Var1, Var2>;
  static_assert(Eval<TestIfExp2, TestEnv1> == Lookup<Var2, TestEnv1>);
}
