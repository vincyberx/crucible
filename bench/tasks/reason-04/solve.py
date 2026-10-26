"""Exact solver for reason-04: dynamic programming over pile sizes."""

MOVES = (2, 5, 6)
N = 200


def main():
    # win[p] is True if the player about to move with p stones left wins with perfect play.
    # p == 0 never starts a turn: it means the previous player took the last stone and
    # lost, so the player "to move" at 0 has already won.
    win = {0: True}
    for p in range(1, N + 1):
        legal = [m for m in MOVES if m <= p]
        if not legal:
            win[p] = False  # rule (b): no legal move -> loses
        else:
            win[p] = any(not win[p - m] for m in legal)
    print(sum(n for n in range(1, N + 1) if not win[n]))


if __name__ == "__main__":
    main()
