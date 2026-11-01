package io.github.progliodario.aethermoor.core

// ICU-like message formatting. Spec: docs/spec/17-localization.md. Reference: tools/reference/i18n.py.
// Arguments are [Long] (integers) or [String].

private fun isSpace(c: Char) = c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\u000C' || c == '\u000B'

private fun pluralCategory(n: Long) = if (n == 1L) "one" else "other"

/** Index of the '}' that closes the '{' at [start], or -1. */
private fun matchingBrace(text: String, start: Int): Int {
    var depth = 0
    for (i in start until text.length) {
        if (text[i] == '{') {
            depth++
        } else if (text[i] == '}') {
            depth--
            if (depth == 0) return i
        }
    }
    return -1
}

private fun splitTopLevelCommas(body: String, limit: Int): List<String> {
    val parts = ArrayList<String>()
    var depth = 0
    var begin = 0
    for (i in body.indices) {
        val ch = body[i]
        if (ch == '{') depth++ else if (ch == '}') depth--
        if (ch == ',' && depth == 0 && parts.size < limit) {
            parts.add(body.substring(begin, i))
            begin = i + 1
        }
    }
    parts.add(body.substring(begin))
    return parts
}

private fun parseBranches(spec: String): Map<String, String>? {
    val branches = HashMap<String, String>()
    var i = 0
    val n = spec.length
    while (i < n) {
        while (i < n && isSpace(spec[i])) i++
        if (i >= n) break
        val start = i
        while (i < n && !isSpace(spec[i]) && spec[i] != '{') i++
        val selector = spec.substring(start, i)
        while (i < n && isSpace(spec[i])) i++
        if (selector.isEmpty() || i >= n || spec[i] != '{') return null
        val end = matchingBrace(spec, i)
        if (end < 0) return null
        branches[selector] = spec.substring(i + 1, end)
        i = end + 1
    }
    return branches
}

private fun argToString(value: Any): String = value.toString()

private fun formatArgument(body: String, lang: String, args: Map<String, Any>): String {
    val parts = splitTopLevelCommas(body, 2)
    val name = parts[0].trim { isSpace(it) }
    val verbatim = "{$body}"
    val value = args[name] ?: return verbatim
    if (parts.size == 1) return argToString(value)
    val kind = parts[1].trim { isSpace(it) }
    val branches = (if (parts.size > 2) parseBranches(parts[2]) else null) ?: return verbatim
    if (kind == "plural" && value is Long) {
        val chosen = branches["=$value"] ?: branches[pluralCategory(value)] ?: branches["other"] ?: return ""
        return formatImpl(chosen, lang, args, value)
    }
    if (kind == "select") {
        val chosen = branches[argToString(value)] ?: branches["other"] ?: return ""
        return formatImpl(chosen, lang, args, null)
    }
    return verbatim
}

private fun formatImpl(message: String, lang: String, args: Map<String, Any>, pound: Long?): String {
    val out = StringBuilder()
    var i = 0
    val n = message.length
    while (i < n) {
        val ch = message[i]
        if (ch == '{') {
            if (i + 1 < n && message[i + 1] == '{') {
                out.append('{')
                i += 2
                continue
            }
            val end = matchingBrace(message, i)
            if (end < 0) {
                out.append(message, i, n)
                break
            }
            out.append(formatArgument(message.substring(i + 1, end), lang, args))
            i = end + 1
        } else if (ch == '}' && i + 1 < n && message[i + 1] == '}') {
            out.append('}')
            i += 2
        } else if (ch == '#' && pound != null) {
            out.append(pound)
            i++
        } else {
            out.append(ch)
            i++
        }
    }
    return out.toString()
}

fun formatMessage(message: String, lang: String, args: Map<String, Any> = emptyMap()): String =
    formatImpl(message, lang, args, null)
