"""Message formatting, an ICU-like subset (docs/spec/17-localization.md).

Syntax:
  {name}                                  placeholder (integer or string argument)
  {n, plural, =0 {none} one {# item} other {# items}}
  {kind, select, a {...} b {...} other {...}}
  {{ and }}                               literal braces (top level only)
A placeholder with no matching argument is kept verbatim, e.g. "{name}".
"""
from __future__ import annotations

Arg = int | str


def _plural_category(lang: str, n: int) -> str:
    # Italian and English share the same two categories.
    return "one" if n == 1 else "other"


def _matching_brace(text: str, start: int) -> int:
    """Index of the '}' closing the '{' at `start`, or -1."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _split_top_level_commas(body: str, limit: int) -> list[str]:
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in body:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == "," and depth == 0 and len(parts) < limit:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def _parse_branches(spec: str) -> dict[str, str] | None:
    branches: dict[str, str] = {}
    i = 0
    n = len(spec)
    while i < n:
        while i < n and spec[i].isspace():
            i += 1
        if i >= n:
            break
        start = i
        while i < n and not spec[i].isspace() and spec[i] != "{":
            i += 1
        selector = spec[start:i]
        while i < n and spec[i].isspace():
            i += 1
        if not selector or i >= n or spec[i] != "{":
            return None
        end = _matching_brace(spec, i)
        if end < 0:
            return None
        branches[selector] = spec[i + 1:end]
        i = end + 1
    return branches


def format_message(message: str, lang: str, args: dict[str, Arg], pound: int | None = None) -> str:
    out: list[str] = []
    i = 0
    n = len(message)
    while i < n:
        ch = message[i]
        if ch == "{":
            if i + 1 < n and message[i + 1] == "{":
                out.append("{")
                i += 2
                continue
            end = _matching_brace(message, i)
            if end < 0:
                out.append(message[i:])
                break
            out.append(_format_argument(message[i + 1:end], lang, args))
            i = end + 1
        elif ch == "}" and i + 1 < n and message[i + 1] == "}":
            out.append("}")
            i += 2
        elif ch == "#" and pound is not None:
            out.append(str(pound))
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _format_argument(body: str, lang: str, args: dict[str, Arg]) -> str:
    parts = _split_top_level_commas(body, 2)
    name = parts[0].strip()
    verbatim = "{" + body + "}"
    if name not in args:
        return verbatim
    value = args[name]
    if len(parts) == 1:
        return str(value)
    kind = parts[1].strip()
    branches = _parse_branches(parts[2]) if len(parts) > 2 else None
    if branches is None:
        return verbatim
    if kind == "plural" and isinstance(value, int):
        chosen = branches.get(f"={value}")
        if chosen is None:
            chosen = branches.get(_plural_category(lang, value), branches.get("other"))
        if chosen is None:
            return ""
        return format_message(chosen, lang, args, pound=value)
    if kind == "select":
        chosen = branches.get(str(value), branches.get("other"))
        return "" if chosen is None else format_message(chosen, lang, args)
    return verbatim
