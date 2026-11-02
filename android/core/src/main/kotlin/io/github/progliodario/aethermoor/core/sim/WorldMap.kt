package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.GeneratedWorld
import io.github.progliodario.aethermoor.core.WorldParams
import io.github.progliodario.aethermoor.core.faunaAt

/** The map of a streamed world: only its size, the spawn and the NPCs (tiles, props and enemies come from the chunks). */
fun makeStreamMap(params: WorldParams): TileMap {
    val cx = params.width / 2
    val cy = params.height / 2
    return TileMap(
        width = params.width,
        height = params.height,
        tilesetId = "base:tileset/overworld",
        ground = IntArray(0),
        spawnX = (cx * 256 + 128) / 256f,
        spawnY = (cy * 256 + 128) / 256f,
        props = emptyList(),
        npcs = params.npcs.map {
            NpcPoint(it.key, it.dialogue, it.variant, ((cx + it.dx) * 256 + 128) / 256f, ((cy + it.dy) * 256 + 128) / 256f)
        },
    )
}

/** Turns a generated world into the tile map the simulation plays on. */
fun makeTileMap(world: GeneratedWorld, params: WorldParams, seed: ULong): TileMap =
    TileMap(
        width = world.width,
        height = world.height,
        tilesetId = "base:tileset/overworld",
        ground = world.tiles,
        spawnX = world.spawnX256 / 256f,
        spawnY = world.spawnY256 / 256f,
        props = world.props.map { Prop(it.art, it.x256 / 256f, it.y256 / 256f, it.radiusX100 / 100f) },
        spawners = world.spawners.map { SpawnPoint(faunaAt(seed, params, it.first, it.second).enemy, it.first + 0.5f, it.second + 0.5f) },
        npcs = world.npcs.map { NpcPoint(it.key, it.dialogue, it.variant, it.x256 / 256f, it.y256 / 256f) },
    )
