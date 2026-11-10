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

get_filename_component(AETHER_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)

find_package(SDL3 CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

# Strict warnings and deterministic floating point (see ADR 0005): no fast-math, no FMA contraction.
function(aether_target_options target)
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /WX /permissive- /fp:strict)
  else()
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
  endif()
endfunction()

# Headless core: must not depend on SDL, graphics, audio, input or UI.
add_library(aether_core STATIC
  src/core/version.cpp
  src/core/numerics.cpp
  src/core/rules.cpp
  src/core/id.cpp
  src/core/message_format.cpp
  src/core/worldgen.cpp
  src/core/worldtime.cpp)
target_include_directories(aether_core PUBLIC src)
target_compile_definitions(aether_core PUBLIC
  AETHER_GAME_NAME="${AETHER_NAME}"
  AETHER_GAME_VERSION="${AETHER_VERSION}")
aether_target_options(aether_core)

# Content packs: JSON loading. Still headless.
add_library(aether_data STATIC src/data/pack.cpp src/data/protagonist.cpp src/data/world_data.cpp)
target_link_libraries(aether_data PUBLIC aether_core PRIVATE nlohmann_json::nlohmann_json)
aether_target_options(aether_data)

# Vector art: recipes, software rasterizer, rigs and clips. Headless (produces RGBA8 bitmaps).
add_library(aether_vector STATIC src/vector/recipe.cpp src/vector/raster.cpp src/vector/rig.cpp)
target_link_libraries(aether_vector PUBLIC aether_core PRIVATE nlohmann_json::nlohmann_json)
aether_target_options(aether_vector)

# Sound: the synthesizer of the sound effects (spec 14). Headless (produces 16 bit samples).
add_library(aether_audio STATIC src/audio/synth.cpp src/audio/director.cpp src/audio/events.cpp src/audio/music.cpp)
target_link_libraries(aether_audio PUBLIC aether_core PRIVATE nlohmann_json::nlohmann_json)
aether_target_options(aether_audio)

# Simulation: tile maps, movement, collisions, the M2 world. Headless.
add_library(aether_sim STATIC
  src/sim/tilemap.cpp src/sim/movement.cpp src/sim/combat.cpp src/sim/story.cpp src/sim/save.cpp src/sim/save_bundle.cpp src/sim/profile.cpp src/sim/combat_loader.cpp src/sim/world.cpp src/sim/world_map.cpp src/sim/chunk_store.cpp)
target_link_libraries(aether_sim PUBLIC aether_core aether_data PRIVATE nlohmann_json::nlohmann_json)
aether_target_options(aether_sim)

add_executable(aethermoor src/app/main.cpp src/app/texture_cache.cpp src/app/sound_board.cpp)
target_link_libraries(aethermoor PRIVATE aether_core aether_data aether_vector aether_audio aether_sim SDL3::SDL3)
target_compile_definitions(aethermoor PRIVATE AETHER_REPO_ROOT="${AETHER_REPO_ROOT}")
aether_target_options(aethermoor)

# Ship the shared data next to the executable.
add_custom_command(TARGET aethermoor POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
          "${CMAKE_CURRENT_SOURCE_DIR}/../data" "$<TARGET_FILE_DIR:aethermoor>/data")

enable_testing()

find_package(Catch2 3 CONFIG REQUIRED)

add_executable(aether_tests
  tests/version_test.cpp
  tests/conformance_test.cpp
  tests/pack_test.cpp
  tests/sim_test.cpp
  tests/combat_test.cpp)
target_link_libraries(aether_tests PRIVATE aether_core aether_data aether_vector aether_audio aether_sim
                                           nlohmann_json::nlohmann_json Catch2::Catch2WithMain)
target_compile_definitions(aether_tests PRIVATE AETHER_REPO_ROOT="${AETHER_REPO_ROOT}")
add_test(NAME unit COMMAND aether_tests)

# Smoke test: opens a window with the dummy video driver, bakes the art and walks the player.
add_test(NAME smoke COMMAND aethermoor --smoke-test --map=demo --screenshot-dir=${CMAKE_BINARY_DIR}/screenshots)
add_test(NAME smoke_world COMMAND aethermoor --smoke-test --map=world --screenshot-dir=${CMAKE_BINARY_DIR}/screenshots_world)
# A village of the world seen from its road (seed 1234: the village at tile 7520,7592).
add_test(NAME smoke_settlement COMMAND aethermoor --smoke-test --map=world --start=7520.5,7598.5
         --screenshot-dir=${CMAKE_BINARY_DIR}/screenshots_settlement)
set_tests_properties(smoke smoke_world smoke_settlement PROPERTIES
  ENVIRONMENT "SDL_VIDEODRIVER=dummy;SDL_RENDER_DRIVER=software"
  TIMEOUT 60)
