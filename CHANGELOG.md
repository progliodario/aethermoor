# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added

- M4a: quests, dialogue, conditions and effects (spec 07). The guild clerk Mira offers the slime quest; NPCs, interaction (E, gamepad X, touch button), dialogue box with choices, quest tracker and gold on both clients; shared `story` scenarios.
- M3: real-time combat slice. Sword swing with an arc hitbox, slimes that chase, strike and return, damage numbers, XP and level-ups, loot, a HUD, 12 slimes on the demo map; shared combat scenarios (suite `combat`) run by both clients; spec 05.
- M2: in-house vector rasterizer, rigs and clips, tile map (Tiled TMJ), player movement and collisions, camera, demo map and art; the desktop (SDL3) and Android (libGDX) clients draw and move a vector character; conformance suites rig_pose, movement and raster; specs 02, 03, 13, 16; ADR 0012.
- M1: spec 00, 01, 04 (formulas), 12 (draft) and 17; Python reference (RNG, hash, noise, stats, damage, XP, message format, IDs); conformance vectors; JSON schemas and sample content; pack loader and the same numerics in C++ and Kotlin, both running the shared vectors.
- M0: repository foundations (docs, ADRs, schemas, data validation, CI workflows, desktop and Android skeletons).
