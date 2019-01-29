#include "ThirdParty/ctre.hpp"

#include <iostream>
#include <optional>
#include <string_view>
#include <type_traits>
#include <utility>

using namespace ctre::literals;

using namespace std::string_view_literals;

struct name {
  bool has;
  std::string_view first, family;
};

static constexpr std::optional<std::string_view> lexit(std::string_view s) {
  auto [re, m] = "^([A-Za-z]+)"_ctre.search(s);

  if (re) {
    return s.substr(m.size());
  }

  return std::nullopt;
}

struct Word {};
struct Number {};
struct LexError {};
struct StopSymbol {};

static constexpr auto word_regex = "^([A-Za-z]+)"_ctre;
static constexpr auto number_regex = "^([\\d]+)"_ctre;

static constexpr std::optional<std::string_view>
MatchesWord(std::string_view s) {
  if (auto [re, m] = word_regex.search(s); re) {
    return s.substr(m.size());
  }

  return std::nullopt;
}

template <auto &input, class LexedSoFar> struct Lexer {
  static constexpr auto _input = input;
  static constexpr auto matchedWord = MatchesWord(_input);

  using tokens = std::conditional_t<
      matchedWord,
      typename Lexer<*matchedWord, decltype(ctll::push_front(
                                       std::declval<Word>(),
                                       std::declval<LexedSoFar>()))>::results,
      std::conditional_t<_input.size() == 0, LexedSoFar,
                         decltype(
                             ctll::push_front(std::declval<LexError>(),
                                              std::declval<LexedSoFar>()))>>;
};

template <auto &input>
using Tokens = typename Lexer<input, ctll::empty_list>::tokens;

int main() {
  {
    constexpr std::string_view s{"abc123"};
    constexpr auto res = lexit(s);
    static_assert(res.has_value());

    std::cout << *res << "\n";
  }

  constexpr auto ct_string = ctll::basic_fixed_string{"abc123"};
  using tokens = Tokens<decltype(ct_string)>;

  return 0;
}
