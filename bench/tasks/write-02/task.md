# Task: incident summary from raw channel notes

Write the executive incident summary for incident INC-2291 from the raw notes below.

## Raw notes (exported from the incident channel, 14 September 2026)

Staff in Milan post in CEST (UTC+2); everyone else posts in UTC. Times are as posted.

```
[09:52 CEST] Priya Nair: starting deploy of payments-api v3.18.0 (includes DB migration 0147)
[07:55 UTC]  (added later from logs) first customer-facing failure: HTTP 500 on POST /checkout
[07:58 UTC]  PagerDuty: checkout error rate 14% (threshold 2%), paging on-call
[10:01 CEST] Marco Bellini: ack, looking
[08:07 UTC]  Priya Nair: rolling back to v3.17.4
[08:10 UTC]  Support lead: rough guess, ~3,000 customers affected?
[08:19 UTC]  rollback finished, error rate still 6%
[10:26 CEST] Marco Bellini: found it. migration 0147 added a NOT NULL column risk_score to
             orders with no default. v3.17.4 doesn't know the column, so every insert
             fails. The rollback reverted the code, not the schema.
[08:41 UTC]  Marco Bellini: applied DEFAULT 0 to orders.risk_score by hand
[08:44 UTC]  error rate back to 0.3% baseline. Customer impact over.
[11:30 CEST] Finance: final number from billing: 2,371 unique customers had at least one
             failed checkout. 412 of them retried successfully later the same day.
[12:05 UTC]  Follow-ups agreed in the review (priority set by the engineering manager):
             - P1: CI check that blocks migrations adding NOT NULL columns without a
               default. Owner: Release Engineering. Due 2026-09-30.
             - P1: Rollback runbook must cover schema changes (expand/contract
               migrations). Owner: Payments team. Due 2026-10-07.
             - P2: Lower the checkout error alert threshold to 1%. Owner: SRE team.
               Due 2026-10-14.
             - P1: Alert when the error rate stays elevated after a rollback.
               Owner: SRE team. Due 2026-10-07.
             - P2: Automatic status-page updates. Owner: Support. Due 2026-10-31.
```

## Requirements

1. At most **200 words** in total.
2. Use exactly these six section labels, in this order, each at the start of its own line
   and followed by a colon: `Summary`, `Impact`, `Duration`, `Root cause`, `Detection`,
   `Action items`.
3. **All times in UTC**, written as `HH:MM UTC`. Do not use CEST anywhere.
4. **Duration** is measured from the first customer-facing failure to the moment customer
   impact ended; state it in minutes together with its start and end times.
5. Use final figures, not early estimates.
6. **Blameless:** do not name any individual person anywhere in the summary.
7. **Action items:** list only the P1 follow-ups, each with its owning team and due date.
8. The root cause must explain why the rollback did not end the impact.

## Deliverable

Write the summary to `ANSWER.md` in the current directory. The file must contain only
the summary.
