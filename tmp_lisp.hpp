#pragma once

template <bool b> struct BoolConst { };

using True = BoolConst<true>;
using False = BoolConst<false>;

template <int i> struct IntConst { };

template <int i> struct Var {};

template <class Variable, class Value> struct Binding {};

template <class... Bindings> struct Env {};

using EmptyEnv = Env<>;

namespace detail {
template <class T0, class T1> struct Concat;

template <class... Bindings1, class... Bindings2>
struct Concat<Env<Bindings1...>, Env<Bindings2...>> {
  using Result = Env<Bindings1..., Bindings2...>;
};

template <class... Ts> struct List {};

template <class, class> struct MakeEnv;

template <> struct MakeEnv<List<>, List<>> { using Result = EmptyEnv; };

template <class Variable, class... Variables, class Value, class... Values>
struct MakeEnv<List<Variable, Variables...>, List<Value, Values...>> {
  static_assert(sizeof...(Variables) == sizeof...(Values));
  using InitialEnv = Env<Binding<Variable, Value>>;
  using FinalEnv =
      typename MakeEnv<List<Variables...>, List<Values...>>::Result;
  using Result = typename Concat<InitialEnv, FinalEnv>::Result;
};
} // namespace detail

template <class Variables, class Values>
using MakeEnv_t = typename detail::MakeEnv<Variables, Values>::Result;

template <class Env1, class Env2>
using ExtendEnv_t = typename detail::Concat<Env1, Env2>::Result;

enum class OpCode { Add, Sub, Mul, Eq, Leq };

template <OpCode op> struct Op {};

template <class OperatorExp, class... OperandExps> struct ApplicationExp {};

template <int i> using Param = Var<i>;

template <class Body, class Environment, class... Params> struct Lambda {};

template <class T> using Result_t = typename T::Result;

template <class Variable, class Env> struct Lookup;

/*
TODO TRY NEXT: try extending the environment in the return value
*/

template <class Value, class Environment> struct PushEnv {
  using Result = Value;
};

template <class LambdaBody, class LambdaEnv, class... LambdaParams,
          class Environment>
struct PushEnv<Lambda<LambdaBody, LambdaEnv, LambdaParams...>, Environment> {
   using Result =
       Lambda<LambdaBody, ExtendEnv_t<LambdaEnv, Environment>,
       LambdaParams...>;
};

template <class Variable, class Value, class... Bindings>
struct Lookup<Variable, Env<Binding<Variable, Value>, Bindings...>> {
  using Result = Value;
};

template <class Variable, class Binding0, class... Bindings>
struct Lookup<Variable, Env<Binding0, Bindings...>> {
  using Result = Result_t<Lookup<Variable, Env<Bindings...>>>;
};

template <class Variable, class Env>
using Lookup_t =
  typename PushEnv<typename Lookup<Variable, Env>::Result, Env>::Result;

template <class Cond, class IfTrue, class IfFalse> struct IfExp {};

template <class Operator, class... Operands> struct Apply;

/*****************
      EVAL
 *****************/

template <class Exp, class Env> struct Eval;

template <int i, class Env> struct Eval<IntConst<i>, Env> {
  using Result = IntConst<i>;
};

template <bool b, class Env> struct Eval<BoolConst<b>, Env> {
  using Result = BoolConst<b>;
};

template <int i, class Env> struct Eval<Var<i>, Env> {
  using Result = Lookup_t<Var<i>, Env>;
};

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<Cond, IfTrue, IfFalse>, Env>;

template <class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<True, IfTrue, IfFalse>, Env> {
  using Result = Result_t<Eval<IfTrue, Env>>;
};

template <class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<False, IfTrue, IfFalse>, Env> {
  using Result = Result_t<Eval<IfFalse, Env>>;
};

template <int i, class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<IntConst<i>, IfTrue, IfFalse>, Env> {
  using Result = Result_t<Eval<IfTrue, Env>>;
};

template <class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<IntConst<0>, IfTrue, IfFalse>, Env> {
  using Result = Result_t<Eval<IfFalse, Env>>;
};

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval<IfExp<Cond, IfTrue, IfFalse>, Env> {
  using Result =
      Result_t<Eval<IfExp<Result_t<Eval<Cond, Env>>, IfTrue, IfFalse>, Env>>;
};

template <class Body, class LambdaEnv, class... Params, class Env>
struct Eval<Lambda<Body, LambdaEnv, Params...>, Env> {
  using Result = Lambda<Body, ExtendEnv_t<LambdaEnv, Env>, Params...>;
};

template <class OperatorExp, class... OperandExps, class Env>
struct Eval<ApplicationExp<OperatorExp, OperandExps...>, Env> {
  using Result =
      typename Apply<typename Eval<OperatorExp, Env>::Result,
                     typename Eval<OperandExps, Env>::Result...>::Result;
};

template <OpCode opcode, class... OperandExps, class Env>
struct Eval<ApplicationExp<Op<opcode>, OperandExps...>, Env> {
  using Result =
      typename Apply<Op<opcode>,
                     typename Eval<OperandExps, Env>::Result...>::Result;
};

template <class Exp, class Env> using Eval_r = Result_t<Eval<Exp, Env>>;

/*****************
      APPLY
 *****************/

template <int i1, int i2>
struct Apply<Op<OpCode::Add>, IntConst<i1>, IntConst<i2>> {
  using Result = IntConst<i1 + i2>;
};

template <int i1, int i2>
struct Apply<Op<OpCode::Sub>, IntConst<i1>, IntConst<i2>> {
  using Result = IntConst<i1 - i2>;
};

template <int i1, int i2>
struct Apply<Op<OpCode::Mul>, IntConst<i1>, IntConst<i2>> {
  using Result = IntConst<i1 * i2>;
};

template <int i1, int i2>
struct Apply<Op<OpCode::Eq>, IntConst<i1>, IntConst<i2>> {
  using Result = BoolConst<i1 == i2>;
};

template <int i1, int i2>
struct Apply<Op<OpCode::Leq>, IntConst<i1>, IntConst<i2>> {
  using Result = BoolConst<i1 <= i2>;
};

template <class BodyExp, class LambdaEnv, class... Params, class... Args>
struct Apply<Lambda<BodyExp, LambdaEnv, Params...>, Args...> {
  static_assert(sizeof...(Params) == sizeof...(Args));
  using ExtendedEnv =
      ExtendEnv_t<LambdaEnv,
                  MakeEnv_t<detail::List<Params...>, detail::List<Args...>>>;
  using Result = typename Eval<BodyExp, ExtendedEnv>::Result;
};
