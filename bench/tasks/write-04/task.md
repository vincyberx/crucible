# Task: price-change email to existing customers

Write the email announcing a price change for the **Pro** plan of **Lumen Notes**, a
note-taking app, to all existing Pro subscribers. Most of them are not technical.

## Product manager's notes

- Current Pro monthly price: **EUR 8.00 per month**. It increases by **12.5%**.
- The email is sent on **2 November 2026**. For monthly subscribers, the new price applies
  from their first renewal on or after the date exactly **30 days after the send date**.
- Current Pro annual price: **EUR 84.00 per year**. Existing annual subscribers keep
  EUR 84.00 per year until their **first renewal after 30 June 2027**.
- New annual subscribers will pay EUR 94.50 per year. Do **not** mention this price: it
  does not apply to the readers and confuses them.
- Approved reason: the price funds the new offline sync and end-to-end encrypted backups,
  and covers rising server costs.
- Full details page (the only link allowed in the email): https://lumen-notes.example/pricing
- How to cancel: Settings → Billing → Cancel plan. Cancelling takes effect at the end of
  the current billing period, with no fees.
- NOT APPROVED, do not include: "maybe offer a free month to long-time users?",
  "say we are still cheaper than Notion".

## Requirements

1. The first line is the subject: `Subject: ...`, at most 60 characters after `Subject: `,
   and it contains the word "price".
2. The body (everything after the subject line) is **120 to 180 words**.
3. State the new monthly price and the exact date from which it applies.
4. Plain language: do not use any of these words: SKU, ARPU, churn, monetization, tier,
   uplift.
5. No discounts, coupons or free periods; no competitor names.
6. Exactly one link, the details page above.
7. Sign off as `The Lumen Notes team`, with no individual's name.

## Deliverable

Write the email (subject line first, then the body) to `ANSWER.md` in the current
directory. The file must contain only the email.
