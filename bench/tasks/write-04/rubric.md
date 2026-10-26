# Rubric: write-04 (price-change email)

Each criterion is pass/fail and checkable from the text of `ANSWER.md`.

1. The first line starts with `Subject:`; the text after `Subject: ` is at most 60
   characters and contains "price" (case-insensitive).
2. The body (everything after the first line) has between 120 and 180 whitespace-separated
   words, inclusive.
3. The monthly Pro price is stated as changing from EUR 8.00 to **EUR 9.00** per month
   (any clear currency notation such as "€9.00" or "EUR 9" accepted).
4. The new monthly price is stated to apply from the first renewal on or after
   **2 December 2026** (any unambiguous date format, e.g. "2026-12-02").
5. Existing annual subscribers are told they keep **EUR 84.00 per year** until their first
   renewal after **30 June 2027**; "94.50" does not appear.
6. The file contains exactly one URL, and it is `https://lumen-notes.example/pricing`.
7. None of these appears as a whole word or phrase (case-insensitive, plural forms
   included): SKU, ARPU, churn, monetization, tier, uplift, Notion, "free month",
   discount, coupon.
8. The cancellation path Settings → Billing → Cancel plan is given (any arrow or ">"
   separator), and the email ends with the sign-off `The Lumen Notes team` with no
   person's name in the sign-off.
