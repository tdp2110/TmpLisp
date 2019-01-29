#include "ThirdParty/ctre.hpp"
#include <boost/hana.hpp>

#include <iostream>
#include <optional>
#include <string_view>

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

enum class TokenType { Word, Number, LexError, StopSymbol };

template <TokenType> struct Token {};

namespace hana = boost::hana;

static constexpr auto word_regex = "^([A-Za-z]+)"_ctre;
static constexpr auto number_regex = "^([\\d]+)"_ctre;

template <class LexedSoFar>
static constexpr auto lexme_(std::string_view s, LexedSoFar lexed_so_far) {
  if (s.size() == 0) {
    return hana::append(lexed_so_far, TokenType::StopSymbol);
  }
  if (auto [re, m] = word_regex.search(s); re) {
    return lexme_(s.substr(m.size()),
                  hana::append(lexed_so_far, TokenType::Word));
  }
  if (auto [re, m] = number_regex.search(s); re) {
    return lexme_(s.substr(m.size()),
                  hana::append(lexed_so_far, TokenType::Number));
  }
  return hana::append(lexed_so_far, TokenType::LexError);
}

static constexpr auto lexme(std::string_view s) {
  return lexme_(s, hana::make<hana::basic_tuple_tag>());
}

int main() {
  {
    constexpr std::string_view s{"abc123"};
    constexpr auto res = lexit(s);
    static_assert(res.has_value());

    std::cout << *res << "\n";
  }

  lexme("abc123");

  return 0;
}
