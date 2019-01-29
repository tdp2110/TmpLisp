#include "ThirdParty/ctre.hpp"

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

int main() {
  {
    constexpr std::string_view s{"abc123"};
    constexpr auto res = lexit(s);
    static_assert(res.has_value());

    std::cout << *res << "\n";
  }

  return 0;
}
