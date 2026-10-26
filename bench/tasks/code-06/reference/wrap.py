"""Paragraph wrapping with minimum raggedness (reference implementation)."""


def wrap(text, width):
    if not isinstance(width, int) or isinstance(width, bool) or width < 1:
        raise ValueError("width must be an integer >= 1")
    words = text.split()
    n = len(words)
    if n == 0:
        return []

    # best[i] = (cost, lines, end) for the optimal layout of words[i:], where the first
    # line of that layout is words[i:end]. Built from the end of the paragraph backwards,
    # so a tie on (cost, lines) can be broken by the length of the *first* line: that is
    # exactly the lexicographic rule, because every candidate for best[i] differs from the
    # others already in its first line, and the rest is best[end], itself optimal.
    best = [None] * (n + 1)
    best[n] = (0, 0, n)
    for i in range(n - 1, -1, -1):
        choice = None
        length = -1
        for j in range(i + 1, n + 1):
            length += len(words[j - 1]) + 1
            single = j == i + 1
            if length > width and not single:
                break
            if j == n or (single and length > width):
                line_cost = 0
            else:
                line_cost = (width - length) ** 2
            rest_cost, rest_lines, _ = best[j]
            key = (line_cost + rest_cost, 1 + rest_lines, -(j - i))
            if choice is None or key < choice[0]:
                choice = (key, j)
        (cost, lines, _), end = choice
        best[i] = (cost, lines, end)

    out = []
    i = 0
    while i < n:
        end = best[i][2]
        out.append(" ".join(words[i:end]))
        i = end
    return out
