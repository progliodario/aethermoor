#pragma once

// Integer and fixed-point numerics. Spec: docs/spec/01-numerics.md
// Reference: tools/reference/numerics.py. No floating point anywhere in this file.

#include <cstdint>
#include <string_view>

namespace aether {

inline constexpr std::int64_t kOne = 1 << 16;  // 1.0 in Q16.16
inline constexpr std::uint64_t kGolden = 0x9E3779B97F4A7C15ULL;

// Floor division (rounds toward negative infinity). b must not be 0.
constexpr std::int64_t div_floor(std::int64_t a, std::int64_t b) {
    const std::int64_t quotient = a / b;
    const std::int64_t remainder = a % b;
    return (remainder != 0 && ((remainder < 0) != (b < 0))) ? quotient - 1 : quotient;
}

constexpr std::int64_t clamp_i64(std::int64_t value, std::int64_t low, std::int64_t high) {
    return value < low ? low : (value > high ? high : value);
}

// Q16.16 multiplication with floor rounding (arithmetic shift, guaranteed by C++20).
constexpr std::int64_t mulq(std::int64_t a, std::int64_t b) { return (a * b) >> 16; }

std::uint64_t mix64(std::uint64_t z);

class SplitMix64 {
public:
    explicit SplitMix64(std::uint64_t seed) : m_state_(seed) {}
    std::uint64_t next();

private:
    std::uint64_t m_state_;
};

std::uint64_t fnv1a64(std::string_view text);

// Stateless hash of a seed and up to three signed 64-bit integers.
std::uint64_t hash64(std::uint64_t seed, std::int64_t a, std::int64_t b = 0, std::int64_t c = 0);

class Pcg32 {
public:
    Pcg32(std::uint64_t init_state, std::uint64_t init_seq);
    std::uint32_t next_u32();
    // Uniform value in [0, bound) by rejection sampling; bound must be in 1..2^32-1.
    std::uint32_t next_bounded(std::uint32_t bound);

    // For saves: the generator continues exactly where it stopped.
    std::uint64_t state() const { return m_state_; }
    std::uint64_t inc() const { return m_inc_; }
    void set_state(std::uint64_t state, std::uint64_t inc) {
        m_state_ = state;
        m_inc_ = inc;
    }

private:
    std::uint64_t m_state_ = 0;
    std::uint64_t m_inc_ = 0;
};

// Named random stream derived from a master seed ("world", "combat", "loot", ...).
Pcg32 derive_stream(std::uint64_t master_seed, std::string_view name);

// Value noise in Q16.16. Coordinates are Q16.16 integers (may be negative). Results: 0..65535.
std::int64_t lattice(std::uint64_t seed, std::int64_t xi, std::int64_t yi);
std::int64_t fade(std::int64_t t);
std::int64_t lerp_q(std::int64_t a, std::int64_t b, std::int64_t t);
std::int64_t noise2(std::uint64_t seed, std::int64_t x, std::int64_t y);
std::int64_t fbm2(std::uint64_t seed, std::int64_t x, std::int64_t y, int octaves);

}  // namespace aether
