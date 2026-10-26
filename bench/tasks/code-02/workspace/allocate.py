"""Proportional allocation of an amount of cents."""


def allocate(total, weights):
    s = sum(weights)
    shares = [round(total * w / s) for w in weights]
    # make the shares add up
    shares[-1] += total - sum(shares)
    return shares
