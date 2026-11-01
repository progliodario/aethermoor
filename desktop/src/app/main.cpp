// M0 skeleton: opens a window, clears it and shows the game name and version.
// Flags: --version prints the version line; --smoke-test renders a few frames and exits (CI).

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <cstdio>
#include <cstring>
#include <string>

#include "core/version.hpp"

namespace {

constexpr int kWindowWidth = 1280;
constexpr int kWindowHeight = 720;
constexpr int kSmokeTestFrames = 30;

}  // namespace

int main(int argc, char** argv) {
    bool smoke_test = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--version") == 0) {
            std::printf("%s\n", aether::version_line().c_str());
            return 0;
        }
        if (std::strcmp(argv[i], "--smoke-test") == 0) {
            smoke_test = true;
        }
    }

    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return 1;
    }

    const std::string title(aether::game_name());
    SDL_Window* window = nullptr;
    SDL_Renderer* renderer = nullptr;
    if (!SDL_CreateWindowAndRenderer(title.c_str(), kWindowWidth, kWindowHeight,
                                     SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIGH_PIXEL_DENSITY,
                                     &window, &renderer)) {
        SDL_Log("Window creation failed: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    const std::string line = aether::version_line();
    bool running = true;
    int frames = 0;
    while (running) {
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_QUIT ||
                (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE)) {
                running = false;
            }
        }

        SDL_SetRenderDrawColor(renderer, 11, 31, 58, 255);
        SDL_RenderClear(renderer);
        SDL_SetRenderDrawColor(renderer, 111, 227, 255, 255);
        SDL_SetRenderScale(renderer, 3.0F, 3.0F);
        SDL_RenderDebugText(renderer, 16.0F, 16.0F, line.c_str());
        SDL_SetRenderScale(renderer, 1.0F, 1.0F);
        SDL_RenderPresent(renderer);

        if (smoke_test && ++frames >= kSmokeTestFrames) {
            running = false;
        }
        SDL_Delay(8);
    }

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
