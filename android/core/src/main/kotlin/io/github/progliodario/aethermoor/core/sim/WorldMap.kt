package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.GeneratedWorld
import io.github.progliodario.aethermoor.core.WorldParams

/** Turns a generated world into the tile map the simulation plays on. */
fun makeTileMap(world: GeneratedWorld, params: WorldParams): TileMap =
    TileMap(
        width = world.width,
        height = world.height,
        tilesetId = "base:tileset/overworld",
        ground = world.tiles,
        spawnX = world.spawnX256 / 256f,
        spawnY = world.spawnY256 / 256f,
        props = world.props.map { Prop(it.art, it.x256 / 256f, it.y256 / 256f, it.radiusX100 / 100f) },
        spawners = world.spawners.map { SpawnPoint(params.spawnerEnemy, it.first + 0.5f, it.second + 0.5f) },
        npcs = world.npcs.map { NpcPoint(it.key, it.dialogue, it.variant, it.x256 / 256f, it.y256 / 256f) },
    )
