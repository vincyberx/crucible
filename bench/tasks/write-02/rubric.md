# Rubric: write-02 (incident summary)

Each criterion is pass/fail and checkable from the text of `ANSWER.md`.

1. The file has at most 200 words, counting whitespace-separated tokens that contain at least one letter or digit (a lone `-` or `**` is not a word).
2. The six labels `Summary`, `Impact`, `Duration`, `Root cause`, `Detection`,
   `Action items` each start a line (markdown bold or heading markers around them are
   fine), are followed by a colon, and appear in exactly this order.
3. Duration is stated as **49 minutes**, with start **07:55 UTC** and end **08:44 UTC**.
   The string "CEST" does not appear, and every `HH:MM` clock time in the file is
   followed by "UTC".
4. Impact states **2,371** affected customers (`2371` also accepted); the early estimate
   "3,000" / "3000" does not appear.
5. No individual is named: none of "Priya", "Nair", "Marco", "Bellini" appears.
6. Action items lists exactly three items, and they are the three P1 items with matching
   owner and due date: CI check for NOT NULL migrations without default (Release
   Engineering, 2026-09-30); rollback runbook covering schema changes (Payments team,
   2026-10-07); alert on error rate staying elevated after rollback (SRE team, 2026-10-07).
   Neither P2 item (1% alert threshold, status-page updates) appears.
7. Root cause states both that migration 0147 added a NOT NULL column without a default
   and that the rollback reverted the code but not the schema.
8. Detection states that an automated alert fired at 07:58 UTC (3 minutes after the first
   customer-facing failure).
