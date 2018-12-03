#include "tmp_lisp.hpp"

using namespace TmpLisp;

int main() {
  using Zero = IntConst<0>;
  using One = IntConst<1>;
  using Two = IntConst<2>;
  using Three = IntConst<3>;
  
  static_assert(Eval_v<Zero, EmptyEnv> == 0);
  static_assert(Eval_v<One, EmptyEnv> == 1);

  using Var0 = Var<0>;
  using Var1 = Var<1>;
  using Var2 = Var<2>;
  using Var3 = Var<3>;
  using Var4 = Var<4>;
  using MinusOne = IntConst<-1>;
  using MinusTwo = IntConst<-2>;
  using MinusThree = IntConst<-3>;
  using TestEnv1 = Env<Binding<Var0, MinusOne>,
                       Binding<Var1, MinusTwo>,
                       Binding<Var2, MinusThree>,
                       Binding<Var3, True>,
                       Binding<Var4, False>>;
  static_assert(Eval_v<Var0, TestEnv1> == MinusOne::value);
  static_assert(Eval_v<Var1, TestEnv1> == MinusTwo::value);
  static_assert(Eval_v<Var2, TestEnv1> == MinusThree::value);

  using TestIfExp1 = IfExp<Var0, Var1, Var2>;
  static_assert(Eval_v<TestIfExp1, TestEnv1> == Lookup_v<Var1, TestEnv1>);
  static_assert(Lookup_v<Var1, TestEnv1> == MinusTwo::value);

  using TestIfExp2 = IfExp<Zero, Var1, Var2>;
  static_assert(Eval_v<TestIfExp2, TestEnv1> == Lookup_v<Var2, TestEnv1>);
  static_assert(Lookup_v<Var2, TestEnv1> == MinusThree::value);
                
  using TestIfExp3 = IfExp<Var3, Var1, Var2>;
  static_assert(Eval_v<TestIfExp3, TestEnv1> == Lookup_v<Var1, TestEnv1>);

  using TestIfExp4 = IfExp<Var4, Var1, Var2>;
  static_assert(Eval_v<TestIfExp4, TestEnv1> == Lookup_v<Var2, TestEnv1>);

  using TestIfExp5 = IfExp<TestIfExp4, TestIfExp3, TestIfExp2>;
  static_assert(Eval_v<TestIfExp5, TestEnv1> == Eval_v<TestIfExp3, TestEnv1>);

  using TestLambda1 = Lambda<IfExp<Var0, Var1, Var2>,
                             Env<Binding<Var1, One>>,
                             Param<0>,
                             Param<2>>;
  using TestEnv2 = Env<Binding<Var3, Two>>;
  static_assert(Eval_v<ApplicationExp<TestLambda1, Var3, Three>, TestEnv2> == 1);
  static_assert(Eval_v<ApplicationExp<TestLambda1, False, Three>, TestEnv2> == 3);
}
