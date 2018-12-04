#include "tmp_lisp.hpp"

#include <type_traits>


namespace {
template <class T, class U>
inline constexpr bool is_same_v = std::is_same<T, U>::value;
}

int main() {
  using Zero = Int<0>;
  using One = Int<1>;
  using Two = Int<2>;
  using Three = Int<3>;

  static_assert(is_same_v<Eval_t<Zero, EmptyEnv>, Zero>);
  static_assert(is_same_v<Eval_t<One, EmptyEnv>, One>);

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
  static_assert(is_same_v<Eval_t<Var0, TestEnv1>, MinusOne>);
  static_assert(is_same_v<Eval_t<Var1, TestEnv1>, MinusTwo>);
  static_assert(is_same_v<Eval_t<Var2, TestEnv1>, MinusThree>);

  using TestIf1 = If<Var0, Var1, Var2>;
  static_assert(is_same_v<Eval_t<TestIf1, TestEnv1>, Lookup_t<Var1, TestEnv1>>);
  static_assert(is_same_v<Lookup_t<Var1, TestEnv1>, MinusTwo>);

  using TestIf2 = If<Zero, Var1, Var2>;
  static_assert(is_same_v<Eval_t<TestIf2, TestEnv1>, Lookup_t<Var2, TestEnv1>>);
  static_assert(is_same_v<Lookup_t<Var2, TestEnv1>, MinusThree>);

  using TestIf3 = If<Var3, Var1, Var2>;
  static_assert(is_same_v<Eval_t<TestIf3, TestEnv1>, Lookup_t<Var1, TestEnv1>>);

  using TestIf4 = If<Var4, Var1, Var2>;
  static_assert(is_same_v<Eval_t<TestIf4, TestEnv1>, Lookup_t<Var2, TestEnv1>>);

  using TestIf5 = If<TestIf4, TestIf3, TestIf2>;
  static_assert(is_same_v<Eval_t<TestIf5, TestEnv1>, Eval_t<TestIf3, TestEnv1>>);

  using TestLambda1 = Lambda<If<Var0, Var1, Var2>, Env<Binding<Var1, One>>,
                             Param<0>, Param<2>>;
  using TestEnv2 = Env<Binding<Var3, Two>>;
  static_assert(is_same_v<Eval_t<Application<TestLambda1, Var3, Three>, TestEnv2>,
                One>);
  static_assert(is_same_v<Eval_t<Application<TestLambda1, False, Three>, TestEnv2>,
                Three>);

  static_assert(is_same_v<Eval_t<Application<Op<OpCode::Add>, Var0, Var1>,
                Env<Binding<Var0, One>, Binding<Var1, Two>>>, Three>);

  static_assert(is_same_v<Eval_t<Application<Op<OpCode::Mul>, Two, Three>, Env<>>,
                Int<2 * 3>>);

  static_assert(
      is_same_v<Eval_t<Application<Op<OpCode::Eq>, Two, Three>, Env<>>,
                False>);

  using TestFunc2 = Eval_t<Lambda<Application<Op<OpCode::Add>, Var0, Var1>,
                                  Env<Binding<Var0, One>>>,
                           Env<Binding<Var1, Two>>>;
  using TestFunc2CallValue = Eval_t<Application<TestFunc2>, EmptyEnv>;
  static_assert(is_same_v<TestFunc2CallValue, Three>);

  /****************
   Factorial
   ****************/
  
  using FactVar = Var<12345>;
  using Fact =
      Lambda<If<Application<Op<OpCode::Leq>, Var0, Zero>, One,
                   Application<
                       Op<OpCode::Mul>, Var0,
                       Application<FactVar, Application<Op<OpCode::Sub>,
                                                              Var0, One>>>>,
             EmptyEnv, Var0>;

   using ZeroFactorial =
       Eval_t<Application<Fact, Zero>, Env<Binding<FactVar, Fact>>>;

   static_assert(is_same_v<ZeroFactorial, One>);

   using OneFactorial =
       Eval_t<Application<Fact, One>, Env<Binding<FactVar, Fact>>>;

   static_assert(is_same_v<OneFactorial, One>);

   using TwoFactorial =
        Eval_t<Application<Fact, Two>, Env<Binding<FactVar, Fact>>>;

   static_assert(is_same_v<TwoFactorial, Two>);

   using SixFactorial = Eval_t<Application<Fact, Int<6>>,
                               Env<Binding<FactVar, Fact>>>;

   static_assert(is_same_v<SixFactorial, Int<720>>);
   
  /****************
   Tail-recursive Fact
   ****************/

   using XParam = Var<54325>;
   using AccumParam = Var<23424>;
   using FactTailRecInner = Lambda<If<Application<Op<OpCode::Leq>, XParam, Int<0>>,
                                      AccumParam,
                                      Application<FactVar,
                                                  Application<Op<OpCode::Sub>,
                                                              XParam,
                                                              Int<1>>,
                                                  Application<Op<OpCode::Mul>,
                                                              AccumParam,
                                                              XParam>>
                                      >,
                                   EmptyEnv,
                                   XParam,
                                   AccumParam>;

   static_assert(is_same_v<Eval_t<Application<FactTailRecInner, Int<5>, Int<1>>,
                 Env<Binding<FactVar, FactTailRecInner>>>, Int<120>>);

   using Arg = Var<44324>;
   using FactInnerVar = Var<5646>;
   using Fact2 = Lambda<Application<FactInnerVar, Arg, Int<1>>,
                        Env<Binding<FactInnerVar, FactTailRecInner>,
                            Binding<FactVar, FactTailRecInner>>,
                        Arg>;

   static_assert(is_same_v<Eval_t<Application<Fact2, Int<4>>, EmptyEnv>, Int<24>>);
   
  /****************
   Lists
   ****************/

   using SomeVar = Var<2>;
   using SomeValue = Int<404>;
   using AnotherValue = Int<1337>;
   using TestList = Cons<AnotherValue, Cons<SomeVar, Cons<Int<3>, EmptyList>>>;
   using TestEnv = Env<Binding<SomeVar, SomeValue>>;
   
   static_assert(is_same_v<Eval_t<Application<Op<OpCode::Car>, TestList>, TestEnv>, AnotherValue>);

   static_assert(is_same_v<Eval_t<Application<Op<OpCode::Car>,
                 Application<Op<OpCode::Cdr>,
                 TestList>>,
                 TestEnv>,
                 SomeValue>);

   using LenVar = Var<5432>;
   using Param = Var<2342>;
   using Len = Lambda<
     If<Application<Op<OpCode::IsNull>, Param>,
        Int<0>,
        Application<Op<OpCode::Add>,
                    Int<1>,
                    Application<LenVar,
                                Application<Op<OpCode::Cdr>, Param>>>>,
     EmptyEnv,
     Param>;

   static_assert(
       is_same_v<Eval_t<
           Application<Len,
                       TestList>,
           Env<
               Binding<LenVar, Len>,
               Binding<SomeVar, Bool<false>>
           >
       >,
       Int<3>>);
}
