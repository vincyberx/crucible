# Task: what did the rider pay?

A rider used a contactless transit card from Monday 16 November 2026 to Thursday
26 November 2026 and holds a **concession card**. Using the fare rules below, compute the
total amount the rider paid over the whole log, net of refunds. All amounts are in cents.

## Ride log

Rides are listed in chronological order. Times are the local start time of each ride on a
24-hour clock. These are all the rides the card was used for.

| # | Start | Zones | Note |
|---|-------|-------|------|
| 1 | Mon 16 Nov 08:10 | 4 | |
| 2 | Mon 16 Nov 12:40 | 3 | |
| 3 | Mon 16 Nov 18:00 | 2 | |
| 4 | Tue 17 Nov 07:50 | 3 | |
| 5 | Tue 17 Nov 17:20 | 3 | DELAYED |
| 6 | Wed 18 Nov 08:30 | 4 | |
| 7 | Wed 18 Nov 18:10 | 2 | |
| 8 | Thu 19 Nov 09:00 | 2 | |
| 9 | Thu 19 Nov 16:45 | 4 | |
| 10 | Fri 20 Nov 08:20 | 2 | |
| 11 | Fri 20 Nov 17:40 | 3 | |
| 12 | Sat 21 Nov 11:00 | 3 | |
| 13 | Sun 22 Nov 23:30 | 2 | |
| 14 | Mon 23 Nov 03:10 | 1 | |
| 15 | Mon 23 Nov 04:10 | 3 | |
| 16 | Mon 23 Nov 08:00 | 1 | |
| 17 | Mon 23 Nov 09:30 | 3 | |
| 18 | Tue 24 Nov 07:40 | 1 | |
| 19 | Tue 24 Nov 08:30 | 1 | |
| 20 | Tue 24 Nov 09:20 | 1 | |
| 21 | Tue 24 Nov 13:00 | 2 | |
| 22 | Tue 24 Nov 13:30 | 1 | |
| 23 | Tue 24 Nov 14:00 | 1 | |
| 24 | Tue 24 Nov 14:20 | 2 | |
| 25 | Wed 25 Nov 07:30 | 4 | |
| 26 | Wed 25 Nov 10:00 | 1 | |
| 27 | Wed 25 Nov 12:00 | 3 | DELAYED |
| 28 | Wed 25 Nov 17:45 | 2 | |
| 29 | Thu 26 Nov 03:20 | 3 | |
| 30 | Thu 26 Nov 04:30 | 2 | |
| 31 | Thu 26 Nov 08:15 | 2 | |

## Fare rules

- **F1. Full fare** by number of zones: 1 zone 200, 2 zones 300, 3 zones 400, 4 zones 500.
- **F2. Peak.** A ride is *peak* if it starts on a Monday to Friday at a clock time from
  07:00 to 09:29 inclusive or from 16:30 to 18:59 inclusive (taking the calendar date and
  clock time at which the ride starts). Every other ride is *off-peak*.
- **F3. Price (cheaper of two discounts).** The concession discount takes 80 off the full
  fare and applies to every ride of this rider. The off-peak discount takes 30% off the
  full fare and applies to off-peak rides only. Discounts never combine: the price for a
  zone count is the lowest price obtainable with a single discount that applies.
- **F4. Journeys and transfers.** A ride is a *transfer* if (a) it starts no more than
  90 minutes after the start of the first ride of the current journey, and (b) the current
  journey has had fewer than 2 transfers so far. Every other ride starts a new journey and
  becomes the first ride of the new current journey. Only conditions (a) and (b) decide
  whether a ride is a transfer.
  - The first ride of a journey costs its price (F3).
  - A transfer costs nothing if its zone count is not greater than the highest zone count
    in the journey so far. Otherwise it costs the price for its zone count minus the price
    for the previous highest zone count, where both prices are computed with F3 using the
    peak or off-peak status of the journey's first ride.
- **F5. Service days and weeks.** A service day runs from 04:00 until 03:59 of the next
  calendar day, and a ride belongs to the service day in which it starts (a ride starting
  at 01:30 on a Tuesday belongs to Monday's service day). A service week is the seven
  service days from Monday's to Sunday's.
- **F6. Caps.** The charges counted toward one service day may total at most **700**
  (daily cap), and those counted toward one service week at most **2400** (weekly cap).
  The amount charged for a ride is its cost from F4, reduced if necessary so that neither
  cap is exceeded: `min(cost, 700 − counted so far toward its service day, 2400 − counted
  so far toward its service week)`. Every charge counts toward the caps of the ride's own
  service day and service week.
- **F7. Delay refunds.** A ride marked DELAYED is refunded the amount that was charged for
  it. The refund is made at 04:00 at the end of that ride's service day, that is, after
  every ride of that service day has been charged and before any ride of the next service
  day is processed. From that moment the refunded amount no longer counts toward the
  weekly cap. A refund never changes the charge of a ride that has already been processed.

Process the rides one at a time in chronological order. For each ride: first make any
refunds that are due before it (F7), then decide whether it is a transfer and compute its
cost (F2–F4), then apply the caps (F5–F6).

**Question:** what is the total amount the rider paid, that is, the sum of all charges
minus all refunds?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form, giving the total as an integer number of cents (for
example 12.34 is written `ANSWER: 1234`):

```
ANSWER: <value>
```
