"""Paragraph wrapping."""


def wrap(text, width):
    """Split `text` into lines of at most `width` characters."""
    if not isinstance(width, int) or width < 1:
        raise ValueError("width must be an integer >= 1")
    lines = []
    current = []
    length = 0
    for word in text.split():
        if current and length + 1 + len(word) > width:
            lines.append(" ".join(current))
            current = []
            length = 0
        if current:
            length += 1
        current.append(word)
        length += len(word)
    if current:
        lines.append(" ".join(current))
    return lines
