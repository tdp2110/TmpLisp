//  Restricted Scheme-like Language using Template Metaprogramming
//
//  Copyright Thomas D Peters 2018-present
//
//  Use, modification and distribution is subject to the
//  Boost Software License, Version 1.0. (See accompanying
//  file LICENSE or copy at
//  http://www.boost.org/LICENSE_1_0.txt)

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

template <class Operator, class... Operands> struct SExp {};

template <class Body, class Environment, class... Params> struct Lambda {};

template <class Cond, class IfTrue, class IfFalse> struct If {};

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

/********************
APPLY fwd definition
*********************/

template <class Operator, class... Operands> struct Apply_;

template <class Operator, class... Operands>
using Apply = detail::Result_t<Apply_<Operator, Operands...>>;

/*****************
      EVAL
 *****************/

template <class Exp, class Env> struct Eval_;

template <class Exp, class Env> using Eval = detail::Result_t<Eval_<Exp, Env>>;

template <int i, class Env> struct Eval_<Int<i>, Env> { using type = Int<i>; };

template <bool b, class Env> struct Eval_<Bool<b>, Env> {
  using type = Bool<b>;
};

template <int i, class Env> struct Eval_<Var<i>, Env> {
  using type = Lookup_t<Var<i>, Env>;
};

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval_<If<Cond, IfTrue, IfFalse>, Env>;

template <class IfTrue, class IfFalse, class Env>
struct Eval_<If<True, IfTrue, IfFalse>, Env> {
  using type = Eval<IfTrue, Env>;
};

template <class IfTrue, class IfFalse, class Env>
struct Eval_<If<False, IfTrue, IfFalse>, Env> {
  using type = Eval<IfFalse, Env>;
};

namespace detail {
template <class Val> struct ConvertToBool { using type = True; };

template <> struct ConvertToBool<False> { using type = False; };

template <> struct ConvertToBool<Int<0>> { using type = False; };

template <class Val> using ConvertToBool_t = Result_t<ConvertToBool<Val>>;
} // namespace detail

template <class Cond, class IfTrue, class IfFalse, class Env>
struct Eval_<If<Cond, IfTrue, IfFalse>, Env> {
  using type =
      Eval<If<detail::ConvertToBool_t<Eval<Cond, Env>>, IfTrue, IfFalse>, Env>;
};

template <class Body, class LambdaEnv, class... Params, class Env>
struct Eval_<Lambda<Body, LambdaEnv, Params...>, Env> {
  using type = Lambda<Body, ExtendEnv_t<LambdaEnv, Env>, Params...>;
};

template <class Car, class Cdr, class Env> struct Eval_<Cons<Car, Cdr>, Env> {
  using type = Cons<Eval<Car, Env>, Eval<Cdr, Env>>;
};

template <class Env> struct Eval_<EmptyList, Env> { using type = EmptyList; };

template <OpCode opcode, class Env> struct Eval_<Op<opcode>, Env> {
  using type = Op<opcode>;
};

template <class Operator, class... Operands, class Env>
struct Eval_<SExp<Operator, Operands...>, Env> {
  using type = Apply<Eval<Operator, Env>, Eval<Operands, Env>...>;
};

/*****************
      APPLY
 *****************/

template <> struct Apply_<Op<OpCode::Add>> { using type = Int<0>; };

template <int... is> struct Apply_<Op<OpCode::Add>, Int<is>...> {
  using type = Int<(... + is)>;
};

template <int i1, int i2> struct Apply_<Op<OpCode::Sub>, Int<i1>, Int<i2>> {
  using type = Int<i1 - i2>;
};

template <int... is> struct Apply_<Op<OpCode::Mul>, Int<is>...> {
  using type = Int<(... * is)>;
};

template <> struct Apply_<Op<OpCode::Mul>> { using type = Int<1>; };

template <int... is> struct Apply_<Op<OpCode::Eq>, Int<is>...> {
  using type = Bool<(... == is)>;
};

template <int i1, int i2> struct Apply_<Op<OpCode::Neq>, Int<i1>, Int<i2>> {
  using type = Bool<i1 != i2>;
};

template <int i1, int i2> struct Apply_<Op<OpCode::Leq>, Int<i1>, Int<i2>> {
  using type = Bool<i1 <= i2>;
};

template <int i> struct Apply_<Op<OpCode::Neg>, Int<i>> {
  using type = Int<-i>;
};

template <class... Exps> struct Apply_<Op<OpCode::Eq>, Exps...> {
  using type = Bool<false>;
};

template <bool... bs> struct Apply_<Op<OpCode::Eq>, Bool<bs>...> {
  using type = Bool<(... == bs)>;
};

template <class... Exps> struct Apply_<Op<OpCode::Neq>, Exps...> {
  using type = Bool<true>;
};

template <bool b1, bool b2> struct Apply_<Op<OpCode::Neq>, Bool<b1>, Bool<b2>> {
  using type = Bool<b1 != b2>;
};

template <bool... bs> struct Apply_<Op<OpCode::Or>, Bool<bs>...> {
  using type = Bool<(... or bs)>;
};

template <bool... bs> struct Apply_<Op<OpCode::And>, Bool<bs>...> {
  using type = Bool<(... and bs)>;
};

template <bool b> struct Apply_<Op<OpCode::Not>, Bool<b>> {
  using type = Bool<not b>;
};

template <class Car, class Cdr> struct Apply_<Op<OpCode::Cons>, Car, Cdr> {
  using type = Cons<Car, Cdr>;
};

template <class Car, class Cdr> struct Apply_<Op<OpCode::Car>, Cons<Car, Cdr>> {
  using type = Car;
};

template <class Car, class Cdr> struct Apply_<Op<OpCode::Cdr>, Cons<Car, Cdr>> {
  using type = Cdr;
};

template <class Value> struct Apply_<Op<OpCode::IsNull>, Value> {
  using type = False;
};

template <> struct Apply_<Op<OpCode::IsNull>, EmptyList> { using type = True; };

template <class Body, class Env, class... Params, class... Args>
struct Apply_<Lambda<Body, Env, Params...>, Args...> {
  static_assert(sizeof...(Params) == sizeof...(Args));
  using ExtendedEnv =
      ExtendEnv_t<Env,
                  MakeEnv_t<detail::List<Params...>, detail::List<Args...>>>;
  using type = Eval<Body, ExtendedEnv>;
};

/*****************
  Compound forms
******************/

template <class Env, class Body> using Let = SExp<Lambda<Body, Env>>;

template <class DefaultExp, class... Cases> struct Cond_;

template <class DefaultExp> struct Cond_<DefaultExp> {
  using type = DefaultExp;
};

template <class DefaultExp, class Cond, class IfMatch, class... RemainingCases>
struct Cond_<DefaultExp, Cond, IfMatch, RemainingCases...> {
  using type =
      If<Cond, IfMatch, detail::Result_t<Cond_<DefaultExp, RemainingCases...>>>;
};

template <class DefaultExp, class... Cases>
using Cond = detail::Result_t<Cond_<DefaultExp, Cases...>>;
