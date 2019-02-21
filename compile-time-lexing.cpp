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
    return s.substr(0, m.size());
  }
  return std::nullopt;
}

static constexpr int MatchSize(std::string_view s) noexcept {
  if (auto [re, m] = word_regex.search(s); re) {
    return m.size();
  }
  return -1;
}

template <bool HasValue> struct MaybeSize {
  static constexpr int Call(std::optional<std::string_view> s) {
    return s->size();
  }
};

template <> struct MaybeSize<false> {
  static constexpr int Call(std::optional<std::string_view>) { return 0; }
};

template <bool hasValue, auto &input, class LexedSoFar,
          template <auto &, class> class Lexer>
struct Helper {
  static constexpr auto _input = input;

  static constexpr auto Call(std::optional<std::string_view> matchedWord) {
    return typename Lexer<
        SliceFirst<_input, MaybeSize<true>::Call(matchedWord)>::res,
        decltype(ctll::push_front(std::declval<Word>(),
                                  std::declval<LexedSoFar>()))>::tokens();
  }
};

template <auto &input, class LexedSoFar> struct Lexer {
  static constexpr auto _input = input;
  static constexpr auto matchedWord =
      MatchesWord(std::string_view(_input.begin(), _input.size()));

  using tokens = decltype(
      Helper<matchWord.has_value, _input, LexedSoFar, Lexer>::Call(matcheWord));

  using tokens2 = std::conditional_t<
      matchedWord.has_value(),
      typename Lexer<
          SliceFirst<_input, MaybeSize<matchedWord.has_value()>::Call(
                                 matchedWord)>::res,
          decltype(ctll::push_front(std::declval<Word>(),
                                    std::declval<LexedSoFar>()))>::tokens,
      LexError>;
  // std::conditional_t<_input.size() == 0, LexedSoFar,
  //                    decltype(
  //                        ctll::push_front(std::declval<LexError>(),
  //                                         std::declval<LexedSoFar>()))>>;
};

int main() {
  constexpr std::string_view s{"abc123"};
  constexpr auto res = lexit(s);
  static_assert(res.has_value());

  std::cout << *res << "\n";

  constexpr auto subject = ctll::basic_fixed_string{"asdf"};

  static_assert(MatchesWord(subject.begin()).has_value());

  static constexpr auto s_str = ctll::basic_fixed_string{"frankiedog"};

  {
    constexpr auto slice = SliceFirst<s_str, 1>::res;
    static_assert(slice[0] == 'r');
  }

  {
    constexpr auto slice = SliceFirst<s_str, 2>::res;
    static_assert(slice[0] == 'a');
  }

  {
    static constexpr auto str = ctll::basic_fixed_string{"ab cde"};
    static_assert(str.size() == 6);

    static constexpr int matchSize = MatchSize(str.begin());
    static_assert(matchSize == 2);

    static constexpr auto slice = std::string_view(str.begin()).substr(2);
    static_assert(slice.size() == 4);
    static_assert(slice[0] == ' ');

    static constexpr auto match1 = MatchesWord(str.begin());
    static_assert(match1.has_value());
    static_assert(match1->size() == 2);
    static constexpr auto first = SliceFirst<str, match1->size()>::res;

    static_assert(first.size() == 4);
    static_assert(first[0] == ' ');

    static constexpr auto bla =
        not MatchesWord(std::string_view(first.begin(), first.size()))
                .has_value();
    static_assert(bla);

    // static_assert(MatchSize(first.begin()) == 0);
    static constexpr auto s = std::string_view(first.begin(), first.size());

    // static constexpr auto match2 = MatchesWord(first.begin());
    // static_assert(match2.has_value());

    // static constexpr auto prefix2 = SliceFirst<str, match2->size()>::res;

    using tokens = typename Lexer<str, ctll::empty_list>::tokens;

    // tokens();
  }

  return 0;
}
