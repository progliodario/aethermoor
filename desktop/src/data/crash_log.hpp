#pragma once

#include <cstddef>
#include <deque>
#include <filesystem>
#include <string>
#include <string_view>

namespace aether {

// The crash log (spec 12, "The crash log"): the last messages of the game and the error that stopped it, written as
// a text file in the folder of the saves. Nothing leaves the device. The same in Kotlin (core/CrashLog.kt).
class CrashLog {
public:
    explicit CrashLog(std::size_t keep = 40) : m_keep_(keep) {}

    // A message of the game (a notice shown, a step of the start); only the last `keep` stay.
    void note(std::string line);
    // The text of the file: the version, the error, then the last messages, the oldest first.
    std::string text(std::string_view version, std::string_view error) const;
    // Writes the file; false when it cannot be written.
    bool write(const std::filesystem::path& file, std::string_view version, std::string_view error) const;
    const std::deque<std::string>& lines() const { return m_lines_; }

private:
    std::size_t m_keep_;
    std::deque<std::string> m_lines_;
};

}  // namespace aether
