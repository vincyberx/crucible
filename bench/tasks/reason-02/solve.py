"""Exact solver for reason-02, using Decimal with ROUND_HALF_UP."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

LINES = [
    # (item, category, quantity, unit price)
    ("Atlas of Rivers", "Books", 1, "27.45"),
    ("Night Trains", "Books", 2, "12.35"),
    ("USB-C cable", "Electronics", 3, "4.25"),
    ("Desk lamp", "Home", 1, "23.75"),
    ("Mug", "Home", 2, "6.40"),
    ("Gift card", "Gift card", 1, "20.00"),
]
VAT = {"Books": Decimal("0.04"), "Electronics": Decimal("0.22"),
       "Home": Decimal("0.22"), "Gift card": Decimal("0")}


def r(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def main():
    nets = [(cat, qty * Decimal(price)) for _, cat, qty, price in LINES]
    books_sum = sum(n for cat, n in nets if cat == "Books")
    if books_sum >= Decimal("50.00"):
        nets = [(cat, r(n * Decimal("0.9")) if cat == "Books" else n) for cat, n in nets]
    vat = sum(r(n * VAT[cat]) for cat, n in nets)
    threshold_base = sum(n for cat, n in nets if cat != "Gift card")
    if threshold_base >= Decimal("100.00"):
        shipping = Decimal("0")
    else:
        base = Decimal("6.90")
        shipping = base + r(base * Decimal("0.22"))
    total = sum(n for _, n in nets) + vat + shipping
    print(int((total * 100).to_integral_value()))


if __name__ == "__main__":
    main()
