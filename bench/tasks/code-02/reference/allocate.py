"""Proportional allocation of an amount of cents. Reference implementation."""


def allocate(total, weights):
    weights = list(weights)
    if not weights:
        raise ValueError("weights must not be empty")
    if any(w < 0 for w in weights):
        raise ValueError("weights must be non-negative")
    w_sum = sum(weights)
    if w_sum == 0:
        raise ValueError("at least one weight must be positive")
    if total < 0:
        return [-x for x in allocate(-total, weights)]

    shares = []
    remainders = []
    for i, w in enumerate(weights):
        q, rem = divmod(total * w, w_sum)
        shares.append(q)
        remainders.append((rem, i))
    missing = total - sum(shares)
    # largest remainder first, ties -> lower index first
    order = sorted(remainders, key=lambda ri: (-ri[0], ri[1]))
    for rem, i in order[:missing]:
        shares[i] += 1
    return shares
