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

template <auto &input, size_t offset> class prefix_slice_string {
public:
  static constexpr auto _input = input;
  char content[input.size() - offset];

  template <size_t... I>
  constexpr prefix_slice_string(std::index_sequence<I...>) noexcept
      : content{_input[I + offset]...} {}

  constexpr prefix_slice_string() noexcept
      : prefix_slice_string(
            std::make_index_sequence<_input.size() - offset>()) {}
};

template <auto &input, size_t n> struct SliceFirst {
  static constexpr auto _input = input;
  static_assert(n < input.size());
  static constexpr size_t resLength = input.size() - n;

  static constexpr auto prefix_string = prefix_slice_string<_input, n>();

  static constexpr auto res = ctll::basic_fixed_string{prefix_string.content};
};

static constexpr auto word_regex = "^([A-Za-z]+)"_ctre;
static constexpr auto number_regex = "^([\\d]+)"_ctre;

static constexpr std::optional<std::string_view>
MatchesWord(std::string_view s) noexcept {
  if (auto [re, m] = word_regex.search(s); re) {
    return s.substr(m.size());
  }

  return std::nullopt;
}

template <auto &input, class LexedSoFar> struct Lexer {
  static constexpr auto _input = input;
  static constexpr auto matchedWord = MatchesWord(_input.begin());

  using tokens = decltype(matchedWord);

  /*
using tokens = std::conditional_t<
    matchedWord.has_value(),
    typename Lexer<matchedWord.value(),
                   decltype(ctll::push_front(
                       std::declval<Word>(),
                       std::declval<LexedSoFar>()))>::results,
    std::conditional_t<_input.size() == 0, LexedSoFar,
                       decltype(
                           ctll::push_front(std::declval<LexError>(),
                                            std::declval<LexedSoFar>()))>>;
  */
};

int main() {
  constexpr std::string_view s{"abc123"};
  constexpr auto res = lexit(s);
  static_assert(res.has_value());

  std::cout << *res << "\n";

  constexpr auto subject = ctll::basic_fixed_string{"asdf"};

  static_assert(MatchesWord(subject.begin()).has_value());

  static constexpr auto s2 = ctll::basic_fixed_string{"asdf"};
  // constexpr auto lexed = Lex<s2>();

  using tokens = typename Lexer<s2, ctll::empty_list>::tokens;

  static constexpr auto s_str = ctll::basic_fixed_string{"frankiedog"};

  {
    constexpr auto slice = SliceFirst<s_str, 1>::res;
    static_assert(slice[0] == 'r');
  }

  {
    constexpr auto slice = SliceFirst<s_str, 2>::res;
    static_assert(slice[0] == 'a');
  }

  return 0;
}
