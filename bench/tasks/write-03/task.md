# Task: a dated zero-downtime migration plan

Production Postgres has a table `users` with a column `email` that must be renamed to
`email_address` without downtime. Three services use it: `web`, `worker` and `billing`.
Write the execution plan.

## Steps (fixed; do not split, merge or add steps)

- **S1** Add the nullable column `email_address` to `users`. Non-locking, about 1 minute.
- **S2** Deploy dual-write: all three services write both `email` and `email_address` and
  still read `email`. *Deploy.*
- **S3** Backfill `email_address` from `email` for all existing rows. Non-locking, takes
  **2 hours**.
- **S4** Deploy read switch: all three services read `email_address` (still dual-writing).
  *Deploy.*
- **S5** Add a NOT NULL constraint on `email_address`. *Locks the table.*
- **S6** Deploy write switch: all three services write only `email_address`. *Deploy.*
- **S7** Drop the column `email`. *Locks the table. Irreversible.*
- **S8** Take and verify a full database snapshot. Non-locking, about 10 minutes.
- **S9** Verification query: zero rows with `email_address IS NULL`. Non-locking, about
  5 minutes.

## Constraints

- **C1** S8 must be completed before S1, S3, S5 and S7.
- **C2** S2 requires S1 (the column must exist).
- **C3** S3 may start only after S2 is live; otherwise rows written during the backfill
  are missed.
- **C4** S9 runs after S3 has finished. S4 and S5 both require S9 to have passed.
- **C5** S6 requires both S4 and S5 to be complete (once the old column is no longer
  written, the new one is the only source of truth and must be constrained).
- **C6** S7 requires S6, and S7's date must be at least **7 calendar days** after S6's date.
- **C7** Deploy steps (S2, S4, S6) may run only Monday to Thursday, between 09:00 and
  16:00 UTC, and at most **one deploy per calendar day**.
- **C8** Table-locking steps (S5, S7) may run only inside the weekly maintenance window,
  **every Tuesday 02:00-03:00 UTC**, and at most one locking step per window.
- **C9** Non-deploy, non-locking steps (S1, S3, S8, S9) may run on any day at any time.
- **C10** No step may start before **Monday 2026-11-09 09:00 UTC**.

**Goal:** finish S7 as early as the constraints allow.

## Deliverable

Write the plan to `ANSWER.md` in the current directory, at most **300 words**:
every step with its date (`YYYY-MM-DD`) and start time (`HH:MM UTC`), in execution order,
then a final line `Completion: YYYY-MM-DD`. Mark any irreversible step as irreversible.
