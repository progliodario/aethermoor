package io.github.progliodario.aethermoor.core

/** Replaces `{name}` placeholders. Unknown placeholders are left untouched. */
fun formatPlaceholders(template: String, values: Map<String, String>): String {
    var result = template
    for ((key, value) in values) {
        result = result.replace("{$key}", value)
    }
    return result
}
