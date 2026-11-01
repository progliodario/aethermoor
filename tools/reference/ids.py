"""Content ID validation (docs/spec/00-conventions.md). Written without regex on purpose, so the
C++ and Kotlin clients can implement the exact same algorithm."""
from __future__ import annotations

_LOWER = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"


def _ident(segment: str) -> bool:
    """[a-z][a-z0-9_]*"""
    return (
        len(segment) > 0
        and segment[0] in _LOWER
        and all(c in _LOWER or c in _DIGITS or c == "_" for c in segment)
    )


def _word(segment: str) -> bool:
    """[a-z0-9_]+"""
    return len(segment) > 0 and all(c in _LOWER or c in _DIGITS or c == "_" for c in segment)


def valid_id(text: str) -> bool:
    """namespace:category/name[/more]; namespace and category are identifiers."""
    if text.count(":") != 1:
        return False
    namespace, path = text.split(":")
    if not _ident(namespace):
        return False
    segments = path.split("/")
    if len(segments) < 2 or not _ident(segments[0]):
        return False
    return all(_word(s) for s in segments[1:])
