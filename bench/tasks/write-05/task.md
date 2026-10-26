# Task: vendor recommendation memo for the CFO

Our company needs a transactional email provider. Write a recommendation memo for the CFO
based only on the information below.

## Hard requirements (a vendor that fails any of them is out)

- **H1** All customer data, including logs and metadata, is stored only in the EU.
- **H2** A dedicated sending IP address.
- **H3** An uptime SLA of at least 99.9%.

Volume: **400,000 emails per month**, flat for the next 3 years. Finance has approved a
**36-month commitment** if a vendor offers better terms for one.

## Vendor comparison

| Vendor     | Price                                   | One-time setup | Dedicated IP     | Uptime SLA | Data residency |
|------------|-----------------------------------------|----------------|------------------|------------|----------------|
| Arcmail    | EUR 0.45 per 1,000 emails               | none           | +EUR 30 / month  | 99.95%     | EU region (1)  |
| Brevix     | EUR 220 / month flat, up to 500k emails | EUR 500        | included         | 99.9%      | EU only        |
| Corvo      | EUR 0.60 per 1,000 emails               | none           | +EUR 25 / month  | 99.5%      | EU only        |
| Delta Post | EUR 195 / month flat, up to 600k emails | EUR 1,200      | included         | 99.9%      | EU only        |

(1) Arcmail's EU region stores message content in Frankfurt; delivery logs and account
metadata are replicated to US-East for analytics.

(2) Brevix: with a 36-month commitment, the monthly fee is 15% lower from month 13 onward.
The setup fee is unchanged.

## Requirements for the memo

1. At most **250 words**.
2. Use these headings, in this order: `Recommendation`, `Cost over 36 months`,
   `Why not the others`, `Risks`.
3. Recommend exactly one vendor.
4. Give the total 36-month cost (setup + all monthly charges) of **every vendor that meets
   all hard requirements**, as whole euros.
5. For every excluded vendor, name the hard requirement it fails and why.
6. The `Risks` section has exactly **two** bullet points.

## Deliverable

Write the memo to `ANSWER.md` in the current directory. The file must contain only the memo.
