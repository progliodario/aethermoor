package io.github.progliodario.aethermoor.core

// namespace:category/name[/more]. Spec: docs/spec/00-conventions.md. Reference: tools/reference/ids.py.
// Written without regular expressions so it matches the C++ client exactly.

private fun isLower(c: Char) = c in 'a'..'z'

private fun isDigit(c: Char) = c in '0'..'9'

private fun isWordChar(c: Char) = isLower(c) || isDigit(c) || c == '_'

/** [a-z][a-z0-9_]* */
private fun isIdent(s: String) = s.isNotEmpty() && isLower(s[0]) && s.all(::isWordChar)

/** [a-z0-9_]+ */
private fun isWord(s: String) = s.isNotEmpty() && s.all(::isWordChar)

fun validId(text: String): Boolean {
    if (text.count { it == ':' } != 1) return false
    val colon = text.indexOf(':')
    if (!isIdent(text.substring(0, colon))) return false
    val segments = text.substring(colon + 1).split('/')
    if (segments.size < 2 || !isIdent(segments[0])) return false
    return segments.drop(1).all(::isWord)
}
