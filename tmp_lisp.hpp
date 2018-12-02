#pragma once

namespace TmpLisp {
  template<bool b>
  struct BoolConst {
    static constexpr bool value = b;
  };

  using True = BoolConst<true>;
  using False = BoolConst<false>;
  
  template<int i>
  struct IntConst {
    static constexpr int value = i;
  };

  template<int i>
  struct Var {};

  template<class Variable, class Value>
  struct Binding {};
  
  template<class ... Bindings>
  struct Env {};

  using EmptyEnv  = Env<>;

  namespace detail {
    template<class T0, class T1>
    class Concat;

    template<class ... Bindings1, class ... Bindings2>
    class Concat<Env<Bindings1...>, Env<Bindings2...>>
    {
      using Result = Env<Bindings1..., Bindings2...>;
    };
  }

  template<class Env1, class Env2>
  using ExtendEnv_t = typename detail::Concat<Env1, Env2>::Result;
  
  template<class Variable, class Env>
  struct Lookup;

  template<class Variable, class Value, class ... Bindings>
  struct Lookup<Variable, Env<Binding<Variable, Value>, Bindings...>>
  {
    using Result = Value;
    static constexpr auto value = Result::value;
  };

  template<class OperatorExp, class ... OperandExps>
  struct ApplicationExp {};
  
  template<class Var>
  struct Param;

  template<int i>
  struct Param<Var<i>>
  {
    using Varname = Var<i>;
  };
  
  template<class Body, class Environment, class ... Params>
  struct Lambda {
    constexpr Lambda() = default;
    static constexpr auto value = Lambda();
  };
  
  template<class T>
  using Result_t = typename T::Result;
  
  template<class Variable, class Binding0, class ... Bindings>
  struct Lookup<Variable, Env<Binding0, Bindings...>>
  {
    using Result = Result_t<Lookup<Variable, Env<Bindings...>>>;
    static constexpr auto value = Result::value;
  };
  
  template<class Variable, class Env>
  constexpr auto Lookup_v =  Lookup<Variable, Env>::value;

  template<class Variable, class Env>
  using Lookup_t =  typename Lookup<Variable, Env>::Result;

  template<class Cond, class IfTrue, class IfFalse>
  struct IfExp {};

  template<class Operator, class ... Operands>
  struct Apply;

  /*****************
        EVAL
   *****************/
  
  template<class Exp, class Env>
  struct Eval;

  template<int i, class Env>
  struct Eval<IntConst<i>, Env>
  {
    using Result = IntConst<i>;
    static constexpr auto value = Result::value;
  };

  template<int i, class Env>
  struct Eval<Var<i>, Env>
  {
    using Result = Lookup_t<Var<i>, Env>;
    static constexpr auto value = Result::value;
  };

  template<class Cond, class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<Cond, IfTrue, IfFalse>, Env>;

  template <class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<True, IfTrue, IfFalse>, Env>
  {
    using Result = Result_t<Eval<IfTrue, Env>>;
    static constexpr auto value = Result::value;
  };
  
  template <class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<False, IfTrue, IfFalse>, Env>
  {
    using Result = Result_t<Eval<IfFalse, Env>>;
    static constexpr auto value = Result::value;
  };
  
  template <int i, class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<IntConst<i>, IfTrue, IfFalse>, Env>
  {
    using Result = Result_t<Eval<IfTrue, Env>>;
    static constexpr auto value = Result::value;
  };
  
  template <class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<IntConst<0>, IfTrue, IfFalse>, Env>
  {
    using Result = Result_t<Eval<IfFalse, Env>>;
    static constexpr auto value = Result::value;
  };

  template<class Cond, class IfTrue, class IfFalse, class Env>
  struct Eval<IfExp<Cond, IfTrue, IfFalse>, Env>
  {
    using Result = Result_t<Eval<
                              IfExp<
                                Result_t<Eval<Cond, Env>>,
                                IfTrue,
                                IfFalse>,
                              Env>>;
    static constexpr auto value = Result::value;
  };
  
  template<class Body, class LambdaEnv, class ... Params, class Env>
  struct Eval<Lambda<Body, LambdaEnv, Params...>, Env>
  {
    using Result = Lambda<Body, ExtendEnv_t<LambdaEnv, Env>, Params...>;
    static constexpr auto value = Result::value;
  };

  template<class OperatorExp, class ... OperandExps, class Env>
  struct Eval<ApplicationExp<OperatorExp, OperandExps...>, Env>
  {
    using Result = typename Apply<Eval<OperatorExp, Env>,
                                  Eval<OperandExps, Env>...>::Result;
    static constexpr auto value = Result::Value;
  };
  
  template<class Exp, class Env>
  constexpr auto Eval_v = Eval<Exp, Env>::value;
} // namespace TmpLisp
