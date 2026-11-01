#include "core/numerics.hpp"

#include <initializer_list>

namespace aether {

namespace {

constexpr std::uint64_t kPcgMultiplier = 6364136223846793005ULL;

constexpr std::uint32_t rotate_right32(std::uint32_t value, std::uint32_t rot) {
    return (value >> rot) | (value << ((32U - rot) & 31U));
}

}  // namespace

std::uint64_t mix64(std::uint64_t z) {
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

std::uint64_t SplitMix64::next() {
    m_state_ += kGolden;
    return mix64(m_state_);
}

std::uint64_t fnv1a64(std::string_view text) {
    std::uint64_t h = 0xCBF29CE484222325ULL;
    for (const char ch : text) {
        h ^= static_cast<std::uint8_t>(ch);
        h *= 0x100000001B3ULL;
    }
    return h;
}

std::uint64_t hash64(std::uint64_t seed, std::int64_t a, std::int64_t b, std::int64_t c) {
    std::uint64_t h = seed;
    for (const std::int64_t v : {a, b, c}) {
        h = mix64(h + kGolden + static_cast<std::uint64_t>(v));
    }
    return h;
}

Pcg32::Pcg32(std::uint64_t init_state, std::uint64_t init_seq) {
    m_inc_ = (init_seq << 1) | 1U;
    next_u32();
    m_state_ += init_state;
    next_u32();
}

std::uint32_t Pcg32::next_u32() {
    const std::uint64_t old = m_state_;
    m_state_ = old * kPcgMultiplier + m_inc_;
    const auto xorshifted = static_cast<std::uint32_t>(((old >> 18) ^ old) >> 27);
    const auto rot = static_cast<std::uint32_t>(old >> 59);
    return rotate_right32(xorshifted, rot);
}

std::uint32_t Pcg32::next_bounded(std::uint32_t bound) {
    const std::uint32_t threshold = (0U - bound) % bound;
    for (;;) {
        const std::uint32_t r = next_u32();
        if (r >= threshold) {
            return r % bound;
        }
    }
}

Pcg32 derive_stream(std::uint64_t master_seed, std::string_view name) {
    const std::uint64_t h = fnv1a64(name);
    return Pcg32(mix64(master_seed ^ h), h);
}

std::int64_t lattice(std::uint64_t seed, std::int64_t xi, std::int64_t yi) {
    return static_cast<std::int64_t>(hash64(seed, xi, yi) >> 48);
}

std::int64_t fade(std::int64_t t) { return mulq(mulq(t, t), 3 * kOne - 2 * t); }

std::int64_t lerp_q(std::int64_t a, std::int64_t b, std::int64_t t) { return a + mulq(b - a, t); }

std::int64_t noise2(std::uint64_t seed, std::int64_t x, std::int64_t y) {
    const std::int64_t xi = x >> 16;
    const std::int64_t yi = y >> 16;
    const std::int64_t xf = x & 0xFFFF;
    const std::int64_t yf = y & 0xFFFF;
    const std::int64_t u = fade(xf);
    const std::int64_t v = fade(yf);
    const std::int64_t a = lattice(seed, xi, yi);
    const std::int64_t b = lattice(seed, xi + 1, yi);
    const std::int64_t c = lattice(seed, xi, yi + 1);
    const std::int64_t d = lattice(seed, xi + 1, yi + 1);
    return lerp_q(lerp_q(a, b, u), lerp_q(c, d, u), v);
}

std::int64_t fbm2(std::uint64_t seed, std::int64_t x, std::int64_t y, int octaves) {
    std::int64_t total = 0;
    std::int64_t norm = 0;
    std::int64_t amp = kOne >> 1;
    for (int octave = 0; octave < octaves; ++octave) {
        const std::int64_t scale = std::int64_t{1} << octave;
        const std::int64_t n = noise2(hash64(seed, octave), x * scale, y * scale);
        total += mulq(n, amp);
        norm += amp;
        amp >>= 1;
    }
    return div_floor(total << 16, norm);
}

}  // namespace aether
