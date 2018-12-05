//  Restricted Scheme-like Language using Template Metaprogramming
//
//  Copyright Thomas D Peters 2018-present
//
//  Use, modification and distribution is subject to the
//  Boost Software License, Version 1.0. (See accompanying
//  file LICENSE or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

#include "tmp_lisp.hpp"

#include <type_traits>

template <class T, class U>
inline constexpr bool is_same_v = std::is_same<T, U>::value;

int main() {
  using Zero = Int<0>;
  using One = Int<1>;
  using Two = Int<2>;
  using Three = Int<3>;

  static_assert(is_same_v<Eval<Zero, EmptyEnv>, Zero>);
  static_assert(is_same_v<Eval<One, EmptyEnv>, One>);

  using Var0 = Var<0>;
  using Var1 = Var<1>;
  using Var2 = Var<2>;
  using Var3 = Var<3>;
  using Var4 = Var<4>;
  using MinusOne = Int<-1>;
  using MinusTwo = Int<-2>;
  using MinusThree = Int<-3>;
  using TestEnv1 =
      Env<Binding<Var0, MinusOne>, Binding<Var1, MinusTwo>,
          Binding<Var2, MinusThree>, Binding<Var3, True>, Binding<Var4, False>>;
  static_assert(is_same_v<Eval<Var0, TestEnv1>, MinusOne>);
  static_assert(is_same_v<Eval<Var1, TestEnv1>, MinusTwo>);
  static_assert(is_same_v<Eval<Var2, TestEnv1>, MinusThree>);

  using TestIf1 = If<Var0, Var1, Var2>;
  static_assert(is_same_v<Eval<TestIf1, TestEnv1>, Lookup_t<Var1, TestEnv1>>);
  static_assert(is_same_v<Lookup_t<Var1, TestEnv1>, MinusTwo>);

  using TestIf2 = If<Zero, Var1, Var2>;
  static_assert(is_same_v<Eval<TestIf2, TestEnv1>, Lookup_t<Var2, TestEnv1>>);
  static_assert(is_same_v<Lookup_t<Var2, TestEnv1>, MinusThree>);

  using TestIf3 = If<Var3, Var1, Var2>;
  static_assert(is_same_v<Eval<TestIf3, TestEnv1>, Lookup_t<Var1, TestEnv1>>);

  using TestIf4 = If<Var4, Var1, Var2>;
  static_assert(is_same_v<Eval<TestIf4, TestEnv1>, Lookup_t<Var2, TestEnv1>>);

  using TestIf5 = If<TestIf4, TestIf3, TestIf2>;
  static_assert(is_same_v<Eval<TestIf5, TestEnv1>, Eval<TestIf3, TestEnv1>>);

  using TestLambda1 =
      Lambda<If<Var0, Var1, Var2>, Env<Binding<Var1, One>>, Param<0>, Param<2>>;
  using TestEnv2 = Env<Binding<Var3, Two>>;
  static_assert(is_same_v<Eval<SExp<TestLambda1, Var3, Three>, TestEnv2>, One>);
  static_assert(
      is_same_v<Eval<SExp<TestLambda1, False, Three>, TestEnv2>, Three>);

  static_assert(is_same_v<Eval<SExp<Op<OpCode::Add>, Var0, Var1>,
                               Env<Binding<Var0, One>, Binding<Var1, Two>>>,
                          Three>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Mul>, Two, Three>, Env<>>, Int<2 * 3>>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Eq>, Two, Three>, Env<>>, False>);

  using TestFunc2 =
      Eval<Lambda<SExp<Op<OpCode::Add>, Var0, Var1>, Env<Binding<Var0, One>>>,
           Env<Binding<Var1, Two>>>;
  using TestFunc2CallValue = Eval<SExp<TestFunc2>, EmptyEnv>;
  static_assert(is_same_v<TestFunc2CallValue, Three>);

  static_assert(is_same_v<Eval<SExp<Op<OpCode::Add>>, EmptyEnv>, Int<0>>);

  static_assert(is_same_v<Eval<SExp<Op<OpCode::Mul>>, EmptyEnv>, Int<1>>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Eq>, Int<1>, EmptyList>, EmptyEnv>,
                Bool<false>>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Neq>, Int<1>, EmptyList>, EmptyEnv>,
                Bool<true>>);

  /********
   Variadic ops
   ********/

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Add>, Int<1>, Int<2>, Int<3>>, EmptyEnv>,
                Int<6>>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Mul>, Int<1>, Int<2>, Int<3>>, EmptyEnv>,
                Int<6>>);

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::And>, Bool<true>, Bool<true>, Bool<false>>,
                     EmptyEnv>,
                Bool<false>>);

  static_assert(is_same_v<Eval<SExp<Op<OpCode::Or>, Bool<true>, Bool<true>,
                                    Bool<false>, Bool<false>, Bool<false>>,
                               EmptyEnv>,
                          Bool<true>>);

  static_assert(is_same_v<Eval<SExp<Op<OpCode::Eq>, Bool<true>, Bool<true>,
                                    Bool<true>, Bool<true>, Bool<true>>,
                               EmptyEnv>,
                          Bool<true>>);

  /****************
   Factorial
   ****************/

  using FactVar = Var<12345>;
  using FactExp =
      Lambda<If<SExp<Op<OpCode::Leq>, Var0, Zero>, One,
                SExp<Op<OpCode::Mul>, Var0,
                     SExp<FactVar, SExp<Op<OpCode::Sub>, Var0, One>>>>,
             EmptyEnv, Var0>;

  using ZeroFactorial =
      Eval<SExp<FactExp, Zero>, Env<Binding<FactVar, FactExp>>>;

  static_assert(is_same_v<ZeroFactorial, One>);

  using OneFactorial = Eval<SExp<FactExp, One>, Env<Binding<FactVar, FactExp>>>;

  static_assert(is_same_v<OneFactorial, One>);

  using TwoFactorial = Eval<SExp<FactExp, Two>, Env<Binding<FactVar, FactExp>>>;

  static_assert(is_same_v<TwoFactorial, Two>);

  using SixFactorial =
      Eval<SExp<FactExp, Int<6>>, Env<Binding<FactVar, FactExp>>>;

  static_assert(is_same_v<SixFactorial, Int<720>>);

  /****************
   Tail-recursive Fact
   ****************/

  using XParam = Var<54325>;
  using AccumParam = Var<23424>;
  using FactTailRecInner =
      Lambda<If<SExp<Op<OpCode::Leq>, XParam, Int<0>>, AccumParam,
                SExp<FactVar, SExp<Op<OpCode::Sub>, XParam, Int<1>>,
                     SExp<Op<OpCode::Mul>, AccumParam, XParam>>>,
             EmptyEnv, XParam, AccumParam>;

  static_assert(is_same_v<Eval<SExp<FactTailRecInner, Int<5>, Int<1>>,
                               Env<Binding<FactVar, FactTailRecInner>>>,
                          Int<120>>);

  using Arg = Var<44324>;
  using FactInnerVar = Var<5646>;
  using Fact2 = Lambda<SExp<FactInnerVar, Arg, Int<1>>,
                       Env<Binding<FactInnerVar, FactTailRecInner>,
                           Binding<FactVar, FactTailRecInner>>,
                       Arg>;

  static_assert(is_same_v<Eval<SExp<Fact2, Int<4>>, EmptyEnv>, Int<24>>);

  /******************
     Mutual recursion
  *******************/

  using IsOddVar = Var<4321>;
  using IsEvenVar = Var<994324>;
  using NParam = Var<422340>;
  using IsEvenExp =
      Lambda<If<SExp<Op<OpCode::Eq>, NParam, Int<0>>, Bool<true>,
                SExp<IsOddVar, SExp<Op<OpCode::Sub>, NParam, Int<1>>>>,
             EmptyEnv, NParam>;
  using IsOddExp =
      Lambda<If<SExp<Op<OpCode::Eq>, NParam, Int<0>>, Bool<false>,
                SExp<IsEvenVar, SExp<Op<OpCode::Sub>, NParam, Int<1>>>>,
             EmptyEnv, NParam>;
  using IsOdd =
      Lambda<SExp<IsOddVar, Arg>,
             Env<Binding<IsOddVar, IsOddExp>, Binding<IsEvenVar, IsEvenExp>>,
             Arg>;

  static_assert(is_same_v<Eval<SExp<IsOdd, Int<12>>, EmptyEnv>, Bool<false>>);
  static_assert(is_same_v<Eval<SExp<IsOdd, Int<41>>, EmptyEnv>, Bool<true>>);

  /****************
   Lists
   ****************/

  using SomeVar = Var<2>;
  using SomeValue = Int<404>;
  using AnotherValue = Int<1337>;
  using TestList = Cons<AnotherValue, Cons<SomeVar, Cons<Int<3>, EmptyList>>>;
  using TestEnv = Env<Binding<SomeVar, SomeValue>>;

  static_assert(
      is_same_v<Eval<SExp<Op<OpCode::Car>, TestList>, TestEnv>, AnotherValue>);

  static_assert(
      is_same_v<
          Eval<SExp<Op<OpCode::Car>, SExp<Op<OpCode::Cdr>, TestList>>, TestEnv>,
          SomeValue>);

  using LenVar = Var<5432>;
  using Param = Var<2342>;
  using Len = Lambda<If<SExp<Op<OpCode::IsNull>, Param>, Int<0>,
                        SExp<Op<OpCode::Add>, Int<1>,
                             SExp<LenVar, SExp<Op<OpCode::Cdr>, Param>>>>,
                     EmptyEnv, Param>;

  static_assert(
      is_same_v<Eval<SExp<Len, TestList>,
                     Env<Binding<LenVar, Len>, Binding<SomeVar, Bool<false>>>>,
                Int<3>>);

  /**********************
   Cond
  *********************/

  using CondExp = Cond<SExp<Op<OpCode::Eq>, Int<1>, Var0>, Int<100>,
                       SExp<Op<OpCode::Eq>, Int<2>, Var0>, Int<200>,
                       SExp<Op<OpCode::Eq>, Int<3>, Var0>, Int<300>>;

  static_assert(is_same_v<Eval<CondExp, Env<Binding<Var0, Int<3>>>>, Int<300>>);
  static_assert(
      is_same_v<Eval<CondExp, Env<Binding<Var0, Int<42>>>>, NoMatchError>);

  /**********************
   Let
   **********************/

  using LetExp1 = Let<
      Env<Binding<Var0, One>>,
      Let<Env<Binding<Var1, Two>>, SExp<Op<OpCode::Add>, Var0, Var1, Var2>>>;

  static_assert(is_same_v<Eval<LetExp1, Env<Binding<Var2, Three>>>, Int<6>>);

  using FactArg = Var<4324343>;
  using FactApplication =
      Let<Env<Binding<FactVar, FactExp>>, SExp<FactVar, FactArg>>;

  static_assert(is_same_v<Eval<FactApplication, Env<Binding<FactArg, Int<7>>>>,
                          Int<5040>>);

  /***********************
    higher-order functions
  **********************/

  using MapCarVar = Var<111432>;
  using ListVar = Var<99234>;
  using FuncVar = Var<999434>;

  using MapCarExp =
      Lambda<If<SExp<Op<OpCode::IsNull>, ListVar>, EmptyList,
                Cons<SExp<FuncVar, SExp<Op<OpCode::Car>, ListVar>>,
                     SExp<MapCarVar, FuncVar, SExp<Op<OpCode::Cdr>, ListVar>>>>,
             EmptyEnv, FuncVar, ListVar>;

  using SomeList = Cons<Int<2>, Cons<Int<4>, Cons<Int<6>, EmptyList>>>;
  using DoubleParam = Var<923098>;
  using Double =
      Lambda<SExp<Op<OpCode::Mul>, Int<2>, DoubleParam>, EmptyEnv, DoubleParam>;

  using MappedList = Eval<Let<Env<Binding<MapCarVar, MapCarExp>>,
                              SExp<MapCarVar, Double, SomeList>>,
                          EmptyEnv>;
  static_assert(
      is_same_v<MappedList,
                Cons<Int<4>, Cons<Int<8>, Cons<Int<12>, EmptyList>>>>);

  using FactFun =
      Lambda<SExp<FactVar, FactArg>, Env<Binding<FactVar, FactExp>>, FactArg>;

  using MappedByFact = Eval<SExp<MapCarVar, FactFun, SomeList>,
                            Env<Binding<MapCarVar, MapCarExp>>>;

  static_assert(
      is_same_v<MappedByFact,
                Cons<Int<2>, Cons<Int<24>, Cons<Int<720>, EmptyList>>>>);
}
