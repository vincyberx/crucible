"""Exact solver for reason-05: check every PIN from 0000 to 9999."""

MONTH_LENGTHS_LEAP = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def valid_date(month, day):
    return 1 <= month <= 12 and 1 <= day <= MONTH_LENGTHS_LEAP[month - 1]


def rejected(pin):
    d = [int(c) for c in pin]
    left, right = int(pin[:2]), int(pin[2:])
    r1 = len(set(d)) == 1
    r2 = all(d[i + 1] - d[i] == 1 for i in range(3)) or all(d[i] - d[i + 1] == 1 for i in range(3))
    r3 = valid_date(left, right)          # MMDD
    r4 = valid_date(right, left)          # DDMM
    r5 = pin[:2] == pin[2:]
    r6 = 1940 <= int(pin) <= 2029
    return r1 or r2 or r3 or r4 or r5 or r6


def main():
    print(sum(1 for i in range(10000) if not rejected(f"{i:04d}")))


if __name__ == "__main__":
    main()
