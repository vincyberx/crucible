# Task: a tiny template renderer

The current directory is a small Python 3 project (standard library only).
`template.py` contains a stub `render(template, context)`. Implement it according to the
specification below.

Modify the files in the current directory so that every requirement below is met.
The deliverable is the code in place. You may add tests; do not delete the existing ones.
The existing tests run with `python3 -m unittest discover -s tests -q` from this directory.

## Specification of `render(template: str, context: dict) -> str`

The template is scanned **left to right**.

1. **Literal text** is copied unchanged.
2. **Escapes.** Outside a placeholder, `{{` produces a literal `{` and `}}` produces a
   literal `}`. A single `}` outside a placeholder that is not part of `}}` is an error.
3. **Placeholders.** A `{` that does not start a `{{` escape opens a placeholder, which ends
   at the next `}`. Its content is either `path` or `path|default`:
   - `path` is one or more *names* separated by `.`; each name is a non-empty sequence of
     ASCII letters, digits and underscores (e.g. `user.first_name`, `items.0`). Nothing else
     is allowed in a path: no spaces, no empty names (`a..b`, `.a`, `a.`), no empty path.
   - `default` is everything after the **first** `|` up to the closing `}`. It may be empty
     and may itself contain `|` characters. It may not contain `{`.
   - A `{` anywhere inside a placeholder is an error.
4. **Lookup.** Start from `context`. For each name in the path, the current value must be a
   `dict` that contains that name as a key; otherwise the path is **missing**.
   (Keys are always looked up as strings; `items.0` looks up the key `"0"`.)
5. **Found values** are rendered with `str(value)`. This applies to every found value,
   including falsy ones: `0` renders as `0`, `""` as an empty string, `None` as `None`,
   `False` as `False`. The default is **not** used when the path is found.
6. **Missing paths**: if the placeholder has a default (even an empty one), render the
   default text literally. Without a default, raise `KeyError` whose single argument is the
   path string exactly as written (e.g. `KeyError("user.name")`).
7. **Errors.** Raise `ValueError` for any syntax error: an unclosed placeholder, a stray
   single `}`, an invalid or empty path, or a `{` inside a placeholder.

Examples (`ctx = {"user": {"name": "Ada", "age": 0}, "n": 3}`):

- `Hi {user.name}!` renders as `Hi Ada!`
- `{user.age|unknown}` renders as `0`
- `{user.city|n/a}` renders as `n/a`
- `{{literal}} {n}` renders as `{literal} 3`
