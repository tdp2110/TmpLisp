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

namespace hana = boost::hana;

template <class LexedSoFar>
static constexpr auto lexme_(std::string_view s, LexedSoFar lexed_so_far) {
  if (s.size() == 0) {
    return lexed_so_far;
  }
  if (auto [re, m] = "^([A-Za-z]+)"_ctre.search(s); re) {
    return lexme_(s.substr(m.size()), hana::append(lexed_so_far, Word()));
  }
  if (auto [re, m] = "^([\\d]+)"_ctre.search(s); re) {
    return lexme_(s.substr(m.size()), hana::append(lexed_so_far, Number()));
  }
  return hana::append(lexed_so_far, LexError());
}

static constexpr auto lexme(std::string_view s) {
  return lexme_(s, hana::make_tuple());
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
