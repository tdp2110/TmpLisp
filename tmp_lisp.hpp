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
  struct Env;
  
  using EmptyEnv  = Env<>;

  template<class Variable, class Env>
  struct Lookup;

  template<class Variable, class Value, class ... Bindings>
  struct Lookup<Variable, Env<Binding<Variable, Value>, Bindings...>>
  {
    using Result = Value;
    static constexpr auto value = Result::value;
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
  struct IfExp {
    using Cond_t = Cond;
    using IfTrue_t = IfTrue;
    using IfFalse_t = IfFalse;
  };
  
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
  
  template<class Exp, class Env>
  constexpr auto Eval_v = Eval<Exp, Env>::value;
} // namespace TmpLisp
