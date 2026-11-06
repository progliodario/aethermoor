#include "vector/raster.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <string>
#include <utility>

namespace aether {

namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr int kSubScanlines = 4;

struct Pt {
    float x;
    float y;
};
using Polygon = std::vector<Pt>;

struct Subpath {
    Polygon pts;
    bool closed = false;
};

struct Crossing {
    float x;
    int dir;
};

// ----------------------------------------------------------------------------------- geometry

int circle_segments(float radius_px) { return 16 + 4 * static_cast<int>(std::floor(std::sqrt(radius_px))); }

void append_ellipse(Polygon& out, float cx, float cy, float rx, float ry, int segments) {
    for (int k = 0; k < segments; ++k) {
        const double angle = 2.0 * kPi * static_cast<double>(k) / static_cast<double>(segments);
        out.push_back({static_cast<float>(cx + rx * std::cos(angle)), static_cast<float>(cy + ry * std::sin(angle))});
    }
}

bool is_space_or_comma(char c) { return c == ' ' || c == ',' || c == '\t' || c == '\n' || c == '\r'; }

bool is_letter(char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); }

std::vector<Subpath> parse_path(const std::string& d, float scale) {
    std::vector<Subpath> out;
    Subpath current;
    bool have = false;
    float cur_x = 0.0F;
    float cur_y = 0.0F;
    float start_x = 0.0F;
    float start_y = 0.0F;
    char cmd = 0;
    std::size_t i = 0;

    const auto skip = [&] {
        while (i < d.size() && is_space_or_comma(d[i])) {
            ++i;
        }
    };
    const auto number = [&](float& value) {
        skip();
        if (i >= d.size()) {
            return false;
        }
        const char* begin = d.c_str() + i;
        char* end = nullptr;
        const double parsed = std::strtod(begin, &end);
        if (end == begin) {
            return false;
        }
        i += static_cast<std::size_t>(end - begin);
        value = static_cast<float>(parsed);
        return true;
    };
    const auto ensure_started = [&] {
        if (!have) {
            current = Subpath{};
            current.pts.push_back({cur_x * scale, cur_y * scale});
            have = true;
        }
    };
    const auto add_point = [&](float x, float y) {
        current.pts.push_back({x * scale, y * scale});
        cur_x = x;
        cur_y = y;
    };

    for (;;) {
        skip();
        if (i >= d.size()) {
            break;
        }
        if (is_letter(d[i])) {
            cmd = d[i];
            ++i;
            if (cmd == 'Z') {
                if (have) {
                    current.closed = true;
                    out.push_back(std::move(current));
                    current = Subpath{};
                    have = false;
                }
                cur_x = start_x;
                cur_y = start_y;
            }
            continue;
        }
        float a = 0.0F;
        float b = 0.0F;
        float c = 0.0F;
        float dd = 0.0F;
        float e = 0.0F;
        float f = 0.0F;
        switch (cmd) {
            case 'M':
                if (!number(a) || !number(b)) {
                    return out;
                }
                if (have) {
                    out.push_back(std::move(current));
                }
                current = Subpath{};
                current.pts.push_back({a * scale, b * scale});
                have = true;
                cur_x = start_x = a;
                cur_y = start_y = b;
                cmd = 'L';  // further pairs after M are line-tos
                break;
            case 'L':
                if (!number(a) || !number(b)) {
                    return out;
                }
                ensure_started();
                add_point(a, b);
                break;
            case 'H':
                if (!number(a)) {
                    return out;
                }
                ensure_started();
                add_point(a, cur_y);
                break;
            case 'V':
                if (!number(a)) {
                    return out;
                }
                ensure_started();
                add_point(cur_x, a);
                break;
            case 'Q': {
                if (!number(a) || !number(b) || !number(c) || !number(dd)) {
                    return out;
                }
                ensure_started();
                const float x0 = cur_x;
                const float y0 = cur_y;
                for (int s = 1; s <= 12; ++s) {
                    const float t = static_cast<float>(s) / 12.0F;
                    const float u = 1.0F - t;
                    add_point(u * u * x0 + 2.0F * u * t * a + t * t * c, u * u * y0 + 2.0F * u * t * b + t * t * dd);
                }
                break;
            }
            case 'C': {
                if (!number(a) || !number(b) || !number(c) || !number(dd) || !number(e) || !number(f)) {
                    return out;
                }
                ensure_started();
                const float x0 = cur_x;
                const float y0 = cur_y;
                for (int s = 1; s <= 16; ++s) {
                    const float t = static_cast<float>(s) / 16.0F;
                    const float u = 1.0F - t;
                    add_point(u * u * u * x0 + 3.0F * u * u * t * a + 3.0F * u * t * t * c + t * t * t * e,
                              u * u * u * y0 + 3.0F * u * u * t * b + 3.0F * u * t * t * dd + t * t * t * f);
                }
                break;
            }
            default:
                return out;
        }
    }
    if (have) {
        out.push_back(std::move(current));
    }
    return out;
}

std::vector<Subpath> shape_subpaths(const Shape& shape, float scale) {
    std::vector<Subpath> out;
    switch (shape.kind) {
        case Shape::Kind::Rect: {
            const float x = shape.v[0] * scale;
            const float y = shape.v[1] * scale;
            const float w = shape.v[2] * scale;
            const float h = shape.v[3] * scale;
            Subpath sp;
            sp.closed = true;
            sp.pts = {{x, y}, {x + w, y}, {x + w, y + h}, {x, y + h}};
            out.push_back(std::move(sp));
            break;
        }
        case Shape::Kind::Ellipse: {
            const float rx = shape.v[2] * scale;
            const float ry = shape.v[3] * scale;
            Subpath sp;
            sp.closed = true;
            append_ellipse(sp.pts, shape.v[0] * scale, shape.v[1] * scale, rx, ry, circle_segments(std::max(rx, ry)));
            out.push_back(std::move(sp));
            break;
        }
        case Shape::Kind::Polygon: {
            Subpath sp;
            sp.closed = true;
            for (const auto& p : shape.points) {
                sp.pts.push_back({p.first * scale, p.second * scale});
            }
            out.push_back(std::move(sp));
            break;
        }
        case Shape::Kind::Path:
            out = parse_path(shape.path, scale);
            break;
    }
    return out;
}

float signed_area(const Polygon& poly) {
    float total = 0.0F;
    for (std::size_t i = 0; i < poly.size(); ++i) {
        const Pt& p = poly[i];
        const Pt& q = poly[(i + 1) % poly.size()];
        total += p.x * q.y - q.x * p.y;
    }
    return total * 0.5F;
}

// Round-join, round-cap stroke as a union of positively oriented pieces (see spec 13, step 3).
std::vector<Polygon> stroke_polygons(const std::vector<Subpath>& subpaths, float half_width) {
    std::vector<Polygon> out;
    const auto push_oriented = [&out](Polygon poly) {
        const float area = signed_area(poly);
        if (area == 0.0F) {
            return;
        }
        if (area < 0.0F) {
            std::reverse(poly.begin(), poly.end());
        }
        out.push_back(std::move(poly));
    };
    const int segments = circle_segments(half_width);
    for (const Subpath& sp : subpaths) {
        const std::size_t n = sp.pts.size();
        if (n == 0) {
            continue;
        }
        const std::size_t edges = sp.closed ? n : n - 1;
        for (std::size_t i = 0; i < edges; ++i) {
            const Pt& p0 = sp.pts[i];
            const Pt& p1 = sp.pts[(i + 1) % n];
            const float dx = p1.x - p0.x;
            const float dy = p1.y - p0.y;
            const float length = std::sqrt(dx * dx + dy * dy);
            if (length <= 0.0F) {
                continue;
            }
            const float nx = -dy / length * half_width;
            const float ny = dx / length * half_width;
            push_oriented(
                {{p0.x + nx, p0.y + ny}, {p1.x + nx, p1.y + ny}, {p1.x - nx, p1.y - ny}, {p0.x - nx, p0.y - ny}});
        }
        for (const Pt& p : sp.pts) {
            Polygon circle;
            append_ellipse(circle, p.x, p.y, half_width, half_width, segments);
            push_oriented(std::move(circle));
        }
    }
    return out;
}

// ---------------------------------------------------------------------------------- coverage

void add_span(float* row, int width, float xa, float xb) {
    xa = std::max(xa, 0.0F);
    xb = std::min(xb, static_cast<float>(width));
    if (xb <= xa) {
        return;
    }
    const int first = static_cast<int>(std::floor(xa));
    const int last = std::min(static_cast<int>(std::floor(xb)), width - 1);
    for (int p = first; p <= last; ++p) {
        const float left = std::max(xa, static_cast<float>(p));
        const float right = std::min(xb, static_cast<float>(p + 1));
        if (right > left) {
            row[p] += (right - left) * 0.25F;
        }
    }
}

std::vector<float> coverage(const std::vector<Polygon>& polys, int width, int height) {
    struct Edge {
        float x0, y0, x1, y1;
        int dir;
        float ymin, ymax;
    };
    std::vector<Edge> edges;
    float min_y = 0.0F;
    float max_y = 0.0F;
    bool any = false;
    for (const Polygon& poly : polys) {
        for (std::size_t i = 0; i < poly.size(); ++i) {
            const Pt& p = poly[i];
            const Pt& q = poly[(i + 1) % poly.size()];
            if (!any) {
                min_y = max_y = p.y;
                any = true;
            }
            min_y = std::min({min_y, p.y, q.y});
            max_y = std::max({max_y, p.y, q.y});
            if (p.y == q.y) {
                continue;
            }
            edges.push_back({p.x, p.y, q.x, q.y, q.y > p.y ? 1 : -1, std::min(p.y, q.y), std::max(p.y, q.y)});
        }
    }
    std::vector<float> cov(static_cast<std::size_t>(width) * static_cast<std::size_t>(height), 0.0F);
    if (edges.empty()) {
        return cov;
    }
    const int row_begin = std::max(0, static_cast<int>(std::floor(min_y)));
    const int row_end = std::min(height - 1, static_cast<int>(std::floor(max_y)));
    std::vector<Crossing> crossings;
    for (int r = row_begin; r <= row_end; ++r) {
        float* row = cov.data() + static_cast<std::size_t>(r) * static_cast<std::size_t>(width);
        for (int k = 0; k < kSubScanlines; ++k) {
            const float ys = static_cast<float>(r) + (static_cast<float>(k) + 0.5F) / 4.0F;
            crossings.clear();
            for (const Edge& e : edges) {
                if (ys >= e.ymin && ys < e.ymax) {
                    const float x = e.x0 + (ys - e.y0) * (e.x1 - e.x0) / (e.y1 - e.y0);
                    crossings.push_back({x, e.dir});
                }
            }
            std::sort(crossings.begin(), crossings.end(),
                      [](const Crossing& a, const Crossing& b) { return a.x < b.x || (a.x == b.x && a.dir < b.dir); });
            int winding = 0;
            for (std::size_t i = 0; i < crossings.size(); ++i) {
                if (i > 0 && winding != 0) {
                    add_span(row, width, crossings[i - 1].x, crossings[i].x);
                }
                winding += crossings[i].dir;
            }
        }
    }
    for (float& c : cov) {
        c = std::min(c, 1.0F);
    }
    return cov;
}

// ------------------------------------------------------------------------------------- paint

Color resolve_color(const std::string& text, const Palette& palette) {
    Color color;
    if (text.rfind("$p.", 0) == 0) {
        const auto found = palette.find(std::string_view(text).substr(3));
        if (found != palette.end()) {
            parse_hex_color(found->second, color);
        }
        return color;
    }
    parse_hex_color(text, color);
    return color;
}

struct ResolvedStop {
    float t;
    Color color;
};

struct ResolvedPaint {
    Paint::Kind kind = Paint::Kind::None;
    Color solid;
    float x0 = 0.0F, y0 = 0.0F, x1 = 0.0F, y1 = 0.0F;
    float cx = 0.0F, cy = 0.0F, r = 0.0F;
    std::vector<ResolvedStop> stops;
};

ResolvedPaint resolve_paint(const Paint& paint, const Palette& palette) {
    ResolvedPaint out;
    out.kind = paint.kind;
    if (paint.kind == Paint::Kind::Solid) {
        out.solid = resolve_color(paint.color, palette);
    }
    out.x0 = paint.x0;
    out.y0 = paint.y0;
    out.x1 = paint.x1;
    out.y1 = paint.y1;
    out.cx = paint.cx;
    out.cy = paint.cy;
    out.r = paint.r;
    for (const GradientStop& s : paint.stops) {
        out.stops.push_back({s.t, resolve_color(s.color, palette)});
    }
    return out;
}

float clamp01(float v) { return v < 0.0F ? 0.0F : (v > 1.0F ? 1.0F : v); }

Color color_from_stops(const std::vector<ResolvedStop>& stops, float t) {
    if (stops.empty()) {
        return {};
    }
    if (t <= stops.front().t) {
        return stops.front().color;
    }
    if (t >= stops.back().t) {
        return stops.back().color;
    }
    for (std::size_t i = 0; i + 1 < stops.size(); ++i) {
        const ResolvedStop& s0 = stops[i];
        const ResolvedStop& s1 = stops[i + 1];
        if (t <= s1.t) {
            const float span = s1.t - s0.t;
            const float u = span <= 0.0F ? 0.0F : (t - s0.t) / span;
            return {s0.color.r + (s1.color.r - s0.color.r) * u, s0.color.g + (s1.color.g - s0.color.g) * u,
                    s0.color.b + (s1.color.b - s0.color.b) * u, s0.color.a + (s1.color.a - s0.color.a) * u};
        }
    }
    return stops.back().color;
}

Color paint_at(const ResolvedPaint& paint, float px, float py) {
    switch (paint.kind) {
        case Paint::Kind::Solid:
            return paint.solid;
        case Paint::Kind::Linear: {
            const float dx = paint.x1 - paint.x0;
            const float dy = paint.y1 - paint.y0;
            const float denom = dx * dx + dy * dy;
            const float t = denom <= 0.0F ? 0.0F : clamp01(((px - paint.x0) * dx + (py - paint.y0) * dy) / denom);
            return color_from_stops(paint.stops, t);
        }
        case Paint::Kind::Radial: {
            const float ex = px - paint.cx;
            const float ey = py - paint.cy;
            const float t = paint.r <= 0.0F ? 1.0F : clamp01(std::sqrt(ex * ex + ey * ey) / paint.r);
            return color_from_stops(paint.stops, t);
        }
        case Paint::Kind::None:
            break;
    }
    return {};
}

void composite(std::vector<float>& acc, const std::vector<float>& cov, const ResolvedPaint& paint, float layer_alpha,
               int width, int height, float scale) {
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            const std::size_t index =
                static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x);
            const float c = cov[index];
            if (c <= 0.0F) {
                continue;
            }
            const Color color =
                paint_at(paint, (static_cast<float>(x) + 0.5F) / scale, (static_cast<float>(y) + 0.5F) / scale);
            const float a = (c * layer_alpha) * color.a;
            float* dst = acc.data() + index * 4;
            const float inv = 1.0F - a;
            dst[0] = color.r * a + dst[0] * inv;
            dst[1] = color.g * a + dst[1] * inv;
            dst[2] = color.b * a + dst[2] * inv;
            dst[3] = a + dst[3] * inv;
        }
    }
}

std::uint8_t to_byte(float v) {
    const float scaled = std::floor(v * 255.0F + 0.5F);
    return static_cast<std::uint8_t>(std::max(0.0F, std::min(255.0F, scaled)));
}

}  // namespace

Bitmap rasterize(const Recipe& recipe, float scale, std::string_view variant) {
    Palette palette = recipe.palette;
    const auto found = recipe.variants.find(variant);
    if (found != recipe.variants.end()) {
        for (const auto& [name, value] : found->second) {
            palette[name] = value;
        }
    }

    Bitmap bitmap;
    bitmap.width = std::max(1, static_cast<int>(std::ceil(recipe.width * scale)));
    bitmap.height = std::max(1, static_cast<int>(std::ceil(recipe.height * scale)));
    const std::size_t pixels = static_cast<std::size_t>(bitmap.width) * static_cast<std::size_t>(bitmap.height);
    std::vector<float> acc(pixels * 4, 0.0F);

    const auto listed = [&](const std::vector<std::string>& names) {
        return std::find(names.begin(), names.end(), variant) != names.end();
    };
    for (const Layer& layer : recipe.layers) {
        if ((!layer.only.empty() && !listed(layer.only)) || listed(layer.except)) {
            continue;
        }
        const std::vector<Subpath> subpaths = shape_subpaths(layer.shape, scale);
        if (layer.fill.kind != Paint::Kind::None) {
            std::vector<Polygon> polys;
            for (const Subpath& sp : subpaths) {
                if (sp.pts.size() >= 3) {
                    polys.push_back(sp.pts);
                }
            }
            const std::vector<float> cov = coverage(polys, bitmap.width, bitmap.height);
            composite(acc, cov, resolve_paint(layer.fill, palette), layer.alpha, bitmap.width, bitmap.height, scale);
        }
        if (layer.stroke.present) {
            const std::vector<Polygon> polys = stroke_polygons(subpaths, layer.stroke.width * scale / 2.0F);
            const std::vector<float> cov = coverage(polys, bitmap.width, bitmap.height);
            ResolvedPaint paint;
            paint.kind = Paint::Kind::Solid;
            paint.solid = resolve_color(layer.stroke.color, palette);
            composite(acc, cov, paint, layer.alpha, bitmap.width, bitmap.height, scale);
        }
    }

    bitmap.rgba.assign(pixels * 4, 0);
    for (std::size_t i = 0; i < pixels; ++i) {
        const float* p = acc.data() + i * 4;
        const float a = p[3];
        const std::uint8_t alpha = to_byte(a);
        if (alpha == 0) {
            continue;
        }
        bitmap.rgba[i * 4 + 0] = to_byte(p[0] / a);
        bitmap.rgba[i * 4 + 1] = to_byte(p[1] / a);
        bitmap.rgba[i * 4 + 2] = to_byte(p[2] / a);
        bitmap.rgba[i * 4 + 3] = alpha;
    }
    return bitmap;
}

}  // namespace aether
