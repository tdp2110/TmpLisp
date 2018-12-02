#pragma once

namespace TmpLisp {
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
  struct LookupImpl;

  template<class Variable, class Value, class ... Bindings>
  struct LookupImpl<Variable, Env<Binding<Variable, Value>, Bindings...>>
  {
    static constexpr auto value = Value::value;
  };

  template<class Variable, class Binding0, class ... Bindings>
  struct LookupImpl<Variable, Env<Binding0, Bindings...>>
  {
    static constexpr auto value = LookupImpl<Variable, Env<Bindings...>>::value;
  };
  
  template<class Variable, class Env>
  constexpr auto Lookup =  LookupImpl<Variable, Env>::value;
  
  template<class Exp, class Env>
  struct EvalImpl;

  template<int i, class Env>
  struct EvalImpl<IntConst<i>, Env>
  {
    using Int = IntConst<i>;
    static constexpr auto value = Int::value;
  };

  template<int i, class Env>
  struct EvalImpl<Var<i>, Env>
  {
    using Variable = Var<i>;
    static constexpr auto value = Lookup<Variable, Env>;
  };

  template<class Exp, class Env>
  constexpr auto Eval = EvalImpl<Exp, Env>::value;
} // namespace TmpLisp
