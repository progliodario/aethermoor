cmake_minimum_required(VERSION 3.28)

# Single source of truth for name and version: ../project.json
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/../project.json" AETHER_PROJECT_JSON)
string(JSON AETHER_NAME GET "${AETHER_PROJECT_JSON}" name)
string(JSON AETHER_VERSION GET "${AETHER_PROJECT_JSON}" version)
string(REGEX MATCH "^[0-9]+\\.[0-9]+\\.[0-9]+" AETHER_VERSION_CORE "${AETHER_VERSION}")

project(aethermoor VERSION ${AETHER_VERSION_CORE} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(SDL3 CONFIG REQUIRED)

# Strict warnings and deterministic floating point (see ADR 0005): no fast-math, no FMA contraction.
function(aether_target_options target)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /WX /permissive- /fp:strict)
  else()
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
  endif()
endfunction()

# Headless core: must not depend on SDL, graphics, audio, input or UI.
add_library(aether_core STATIC src/core/version.cpp)
target_include_directories(aether_core PUBLIC src)
target_compile_definitions(aether_core PUBLIC
  AETHER_GAME_NAME="${AETHER_NAME}"
  AETHER_GAME_VERSION="${AETHER_VERSION}")
aether_target_options(aether_core)

add_executable(aethermoor src/app/main.cpp)
target_link_libraries(aethermoor PRIVATE aether_core SDL3::SDL3)
aether_target_options(aethermoor)

# Ship the shared data next to the executable.
add_custom_command(TARGET aethermoor POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
          "${CMAKE_CURRENT_SOURCE_DIR}/../data" "$<TARGET_FILE_DIR:aethermoor>/data")

enable_testing()

find_package(Catch2 3 CONFIG REQUIRED)
add_executable(aether_tests tests/version_test.cpp)
target_link_libraries(aether_tests PRIVATE aether_core Catch2::Catch2WithMain)
add_test(NAME unit COMMAND aether_tests)

# Smoke test: opens a window with the dummy video driver and renders a few frames.
add_test(NAME smoke COMMAND aethermoor --smoke-test)
set_tests_properties(smoke PROPERTIES
  ENVIRONMENT "SDL_VIDEODRIVER=dummy;SDL_RENDER_DRIVER=software"
  TIMEOUT 30)
