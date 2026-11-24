#include "data/crash_log.hpp"

#include <fstream>
#include <utility>

namespace aether {

void CrashLog::note(std::string line) {
    m_lines_.push_back(std::move(line));
    while (m_lines_.size() > m_keep_) {
        m_lines_.pop_front();
    }
}

std::string CrashLog::text(std::string_view version, std::string_view error) const {
    std::string out = "Aethermoor " + std::string(version) + "\nerror: " + std::string(error) + "\n\nlast messages:\n";
    for (const std::string& line : m_lines_) {
        out += "  " + line + "\n";
    }
    return out;
}

bool CrashLog::write(const std::filesystem::path& file, std::string_view version, std::string_view error) const {
    std::ofstream out(file, std::ios::binary | std::ios::trunc);
    if (!out) {
        return false;
    }
    out << text(version, error);
    return static_cast<bool>(out);
}

}  // namespace aether
