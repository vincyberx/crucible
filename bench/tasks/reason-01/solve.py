"""Exact solver for reason-01: brute-force walk over the calendar."""

import datetime as dt

HOLIDAYS = {
    dt.date(2028, 1, 6),
    dt.date(2028, 3, 1),
    dt.date(2028, 3, 19),
    dt.date(2028, 4, 14),
    dt.date(2028, 4, 17),
    dt.date(2028, 4, 25),
    dt.date(2028, 5, 1),
}
ACTIVATION = dt.date(2028, 2, 27)
TRAVEL_DAYS = 40
VALIDITY = 50


def is_travel_day(d):
    return d.weekday() != 6 and d not in HOLIDAYS


def main():
    consumed = 0
    last_usable = None
    for offset in range(VALIDITY):  # calendar days 1..50
        d = ACTIVATION + dt.timedelta(days=offset)
        if not is_travel_day(d):
            continue
        consumed += 1
        if consumed > TRAVEL_DAYS:
            break
        last_usable = d
    print(last_usable.isoformat())


if __name__ == "__main__":
    main()
