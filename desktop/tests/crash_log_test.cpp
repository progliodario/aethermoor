#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

#include "data/crash_log.hpp"

// The crash log (spec 12, "The crash log"): only the last messages stay, and an error forced here writes the file.
TEST_CASE("crash log: an error writes the last messages and the error", "[crash_log]") {
    aether::CrashLog log(3);
    for (int i = 1; i <= 5; ++i) {
        log.note("message " + std::to_string(i));
    }
    REQUIRE(log.lines().size() == 3);
    REQUIRE(log.lines().front() == "message 3");
    const std::filesystem::path file = std::filesystem::temp_directory_path() / "aether_crash_log_test.txt";
    try {
        throw std::runtime_error("forced error");
    } catch (const std::exception& error) {
        REQUIRE(log.write(file, "0.0.0-test", error.what()));
    }
    std::string written;
    {
        std::ifstream in(file, std::ios::binary);
        std::stringstream text;
        text << in.rdbuf();
        written = text.str();
    }
    REQUIRE(written == log.text("0.0.0-test", "forced error"));
    REQUIRE(written.find("error: forced error") != std::string::npos);
    REQUIRE(written.find("message 5") != std::string::npos);
    REQUIRE(written.find("message 2") == std::string::npos);
    std::error_code ec;
    std::filesystem::remove(file, ec);
}
