"""A tiny template renderer: {path}, {path|default}, {{ and }} escapes. Reference."""

import re

_NAME = re.compile(r"[A-Za-z0-9_]+")
_MISSING = object()


def _lookup(context, path):
    current = context
    for name in path.split("."):
        if not isinstance(current, dict) or name not in current:
            return _MISSING
        current = current[name]
    return current


def _validate_path(path):
    if not path:
        raise ValueError("empty path")
    for name in path.split("."):
        if not _NAME.fullmatch(name):
            raise ValueError(f"invalid path: {path!r}")


def render(template, context):
    out = []
    i = 0
    n = len(template)
    while i < n:
        ch = template[i]
        if ch == "{":
            if i + 1 < n and template[i + 1] == "{":
                out.append("{")
                i += 2
                continue
            close = template.find("}", i + 1)
            if close == -1:
                raise ValueError("unclosed placeholder")
            body = template[i + 1:close]
            if "{" in body:
                raise ValueError("'{' inside placeholder")
            if "|" in body:
                path, default = body.split("|", 1)
                has_default = True
            else:
                path, default, has_default = body, "", False
            _validate_path(path)
            value = _lookup(context, path)
            if value is _MISSING:
                if not has_default:
                    raise KeyError(path)
                out.append(default)
            else:
                out.append(str(value))
            i = close + 1
        elif ch == "}":
            if i + 1 < n and template[i + 1] == "}":
                out.append("}")
                i += 2
                continue
            raise ValueError("single '}' outside placeholder")
        else:
            out.append(ch)
            i += 1
    return "".join(out)
