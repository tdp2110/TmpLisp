#pragma once

/*****************
   Builtin Types
 *****************/

template <bool b> struct Bool {};

using True = Bool<true>;
using False = Bool<false>;

template <int i> struct Int {};

template <class Car, class Cdr> struct Cons {};

struct EmptyList {};

template <class Operator, class... Operands> struct Application {};

template <class Body, class Environment, class... Params> struct Lambda {};

template <class Cond, class IfTrue, class IfFalse> struct If {};

/**********************
   Variables, Bindings
***********************/

template <int i> struct Var {};

template <class Variable, class Value> struct Binding {};

template <class... Bindings> struct Env {};

using EmptyEnv = Env<>;

namespace detail {
template <class T0, class T1> struct Concat;

template <class... Bindings1, class... Bindings2>
struct Concat<Env<Bindings1...>, Env<Bindings2...>> {
  using type = Env<Bindings1..., Bindings2...>;
};

template <class... Ts> struct List {};

template <class, class> struct MakeEnv;

template <> struct MakeEnv<List<>, List<>> { using type = EmptyEnv; };

template <class Variable, class... Variables, class Value, class... Values>
struct MakeEnv<List<Variable, Variables...>, List<Value, Values...>> {
  static_assert(sizeof...(Variables) == sizeof...(Values));
  using InitialEnv = Env<Binding<Variable, Value>>;
  using FinalEnv = typename MakeEnv<List<Variables...>, List<Values...>>::type;
  using type = typename Concat<InitialEnv, FinalEnv>::type;
};

template <class T> using Result_t = typename T::type;

} // namespace detail

template <class Variables, class Values>
using MakeEnv_t = typename detail::MakeEnv<Variables, Values>::type;

template <class Env1, class Env2>
using ExtendEnv_t = typename detail::Concat<Env2, Env1>::type;

enum class OpCode {
  Add,
  Sub,
  Mul,
  Eq,
  Neq,
  Leq,
  Neg,
  Or,
  And,
  Not,
  Cons,
  Car,
  Cdr,
  IsNull
};

template <OpCode op> struct Op {};

template <int i> using Param = Var<i>;

template <class Variable, class Env> struct Lookup;

template <class Value, class Environment> struct PushEnv {
  using type = Value;
};

template <class LambdaBody, class LambdaEnv, class... LambdaParams,
          class Environment>
struct PushEnv<Lambda<LambdaBody, LambdaEnv, LambdaParams...>, Environment> {
  using type =
      Lambda<LambdaBody, ExtendEnv_t<LambdaEnv, Environment>, LambdaParams...>;
};

template <class Variable, class Value, class... Bindings>
struct Lookup<Variable, Env<Binding<Variable, Value>, Bindings...>> {
  using type = Value;
};

template <class Variable, class Binding0, class... Bindings>
struct Lookup<Variable, Env<Binding0, Bindings...>> {
  using type = detail::Result_t<Lookup<Variable, Env<Bindings...>>>;
};

template <class Variable, class Env>
using Lookup_t =
    typename PushEnv<typename Lookup<Variable, Env>::type, Env>::type;

template <class Operator, class... Operands> struct Apply;

/*****************
      EVAL
 *****************/

template <class Exp, class Env> struct Eval;

template <int i, class Env> struct Eval<Int<i>, Env> { using type = Int<i>; };

template <bool b, class Env> struct Eval<Bool<b>, Env> {
  using type = Bool<b>;
};

template <int i, class Env> struct Eval<Var<i>, Env> {
  using type = Lookup_t<Var<i>, Env>;
};

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval<If<Cond, IfTrue, IfFalse>, Env>;

template <class IfTrue, class IfFalse, class Env>
struct Eval<If<True, IfTrue, IfFalse>, Env> {
  using type = detail::Result_t<Eval<IfTrue, Env>>;
};

template <class IfTrue, class IfFalse, class Env>
struct Eval<If<False, IfTrue, IfFalse>, Env> {
  using type = detail::Result_t<Eval<IfFalse, Env>>;
};

template <int i, class IfTrue, class IfFalse, class Env>
struct Eval<If<Int<i>, IfTrue, IfFalse>, Env> {
  using type = detail::Result_t<Eval<IfTrue, Env>>;
};

template <class IfTrue, class IfFalse, class Env>
struct Eval<If<Int<0>, IfTrue, IfFalse>, Env> {
  using type = detail::Result_t<Eval<IfFalse, Env>>;
};

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval<If<Cond, IfTrue, IfFalse>, Env> {
  using type = detail::Result_t<
      Eval<If<detail::Result_t<Eval<Cond, Env>>, IfTrue, IfFalse>, Env>>;
};

template <class Body, class LambdaEnv, class... Params, class Env>
struct Eval<Lambda<Body, LambdaEnv, Params...>, Env> {
  using type = Lambda<Body, ExtendEnv_t<LambdaEnv, Env>, Params...>;
};

template <class Car, class Cdr, class Env> struct Eval<Cons<Car, Cdr>, Env> {
  using type =
      Cons<typename Eval<Car, Env>::type, typename Eval<Cdr, Env>::type>;
};

template <class Env> struct Eval<EmptyList, Env> { using type = EmptyList; };

template <class Operator, class... Operands, class Env>
struct Eval<Application<Operator, Operands...>, Env> {
  using type = typename Apply<typename Eval<Operator, Env>::type,
                              typename Eval<Operands, Env>::type...>::type;
};

template <OpCode opcode, class... Operands, class Env>
struct Eval<Application<Op<opcode>, Operands...>, Env> {
  using type =
      typename Apply<Op<opcode>, typename Eval<Operands, Env>::type...>::type;
};

template <class Exp, class Env> using Eval_t = detail::Result_t<Eval<Exp, Env>>;

/*****************
      APPLY
 *****************/

template <> struct Apply<Op<OpCode::Add>> { using type = Int<0>; };

template <int... is> struct Apply<Op<OpCode::Add>, Int<is>...> {
  using type = Int<(... + is)>;
};

template <int i1, int i2> struct Apply<Op<OpCode::Sub>, Int<i1>, Int<i2>> {
  using type = Int<i1 - i2>;
};

template <int... is> struct Apply<Op<OpCode::Mul>, Int<is>...> {
  using type = Int<(... * is)>;
};

template <> struct Apply<Op<OpCode::Mul>> { using type = Int<1>; };

template <int... is> struct Apply<Op<OpCode::Eq>, Int<is>...> {
  using type = Bool<(... == is)>;
};

template <int i1, int i2> struct Apply<Op<OpCode::Neq>, Int<i1>, Int<i2>> {
  using type = Bool<i1 != i2>;
};

template <int i1, int i2> struct Apply<Op<OpCode::Leq>, Int<i1>, Int<i2>> {
  using type = Bool<i1 <= i2>;
};

template <int i> struct Apply<Op<OpCode::Neg>, Int<i>> {
  using type = Int<-i>;
};

template <class... Exps> struct Apply<Op<OpCode::Eq>, Exps...> {
  using type = Bool<false>;
};

template <bool... bs> struct Apply<Op<OpCode::Eq>, Bool<bs>...> {
  using type = Bool<(... == bs)>;
};

template <class... Exps> struct Apply<Op<OpCode::Neq>, Exps...> {
  using type = Bool<true>;
};

template <bool b1, bool b2> struct Apply<Op<OpCode::Neq>, Bool<b1>, Bool<b2>> {
  using type = Bool<b1 != b2>;
};

template <bool... bs> struct Apply<Op<OpCode::Or>, Bool<bs>...> {
  using type = Bool<(... or bs)>;
};

template <bool... bs> struct Apply<Op<OpCode::And>, Bool<bs>...> {
  using type = Bool<(... and bs)>;
};

template <bool b> struct Apply<Op<OpCode::Not>, Bool<b>> {
  using type = Bool<not b>;
};

template <class Car, class Cdr> struct Apply<Op<OpCode::Cons>, Car, Cdr> {
  using type = Cons<Car, Cdr>;
};

template <class Car, class Cdr> struct Apply<Op<OpCode::Car>, Cons<Car, Cdr>> {
  using type = Car;
};

template <class Car, class Cdr> struct Apply<Op<OpCode::Cdr>, Cons<Car, Cdr>> {
  using type = Cdr;
};

template <class Value> struct Apply<Op<OpCode::IsNull>, Value> {
  using type = False;
};

template <> struct Apply<Op<OpCode::IsNull>, EmptyList> { using type = True; };

template <class Body, class Env, class... Params, class... Args>
struct Apply<Lambda<Body, Env, Params...>, Args...> {
  static_assert(sizeof...(Params) == sizeof...(Args));
  using ExtendedEnv =
      ExtendEnv_t<Env,
                  MakeEnv_t<detail::List<Params...>, detail::List<Args...>>>;
  using type = typename Eval<Body, ExtendedEnv>::type;
};
