#include "tmp_lisp.hpp"

using namespace TmpLisp;

int main() {
  using Zero = IntConst<0>;
  using One = IntConst<1>;
  
  static_assert(Eval<Zero, EmptyEnv>::value == 0);
  static_assert(Eval<One, EmptyEnv>::value == 1);
}
