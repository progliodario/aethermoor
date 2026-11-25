package io.github.progliodario.aethermoor.core.vector

/**
 * A level of the graphics quality (spec 13, "Quality"): presentation only, the game is the same at every level. Keep in step with
 * desktop/src/vector/quality.hpp and the table of the spec.
 */
class QualityLevel(
    /** The value of `quality` in the settings file; the text is `ui.quality_<id>`. */
    val id: String,

    /** The largest scale bucket the textures are baked at (spec 13, "Scale buckets and caching"). */
    val bucketCap: Int,

    /** The moving water (spec 13, "Water"). */
    val water: Boolean,

    /** The rounded corners of the ground blending (spec 13, "Ground blending"). */
    val corners: Boolean,

    /** The long shadows of dawn and dusk (spec 08, "The colour of the hour"). */
    val longShadows: Boolean,

    /** All the art of the pack baked once at [bucketCap] fits in this many MiB (tested). */
    val textureBudgetMib: Int,
)

val QUALITY_LEVELS: List<QualityLevel> = listOf(
    QualityLevel("low", 64, water = false, corners = false, longShadows = false, textureBudgetMib = 32),
    QualityLevel("normal", 128, water = true, corners = true, longShadows = true, textureBudgetMib = 128),
    QualityLevel("high", 256, water = true, corners = true, longShadows = true, textureBudgetMib = 512),
)

/** The index of the level [id] in [QUALITY_LEVELS], or [fallback] when there is none. */
fun qualityIndex(id: String?, fallback: Int): Int = QUALITY_LEVELS.indexOfFirst { it.id == id }.takeIf { it >= 0 } ?: fallback
