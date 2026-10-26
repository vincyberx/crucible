# Task: compute an order total exactly

An online shop computes order totals with the rules below. All prices are in euros.

## The order

| Line | Item            | Category    | Quantity | Unit price |
|------|-----------------|-------------|----------|------------|
| 1    | Atlas of Rivers | Books       | 1        | 27.45      |
| 2    | Night Trains    | Books       | 2        | 12.35      |
| 3    | USB-C cable     | Electronics | 3        | 4.25       |
| 4    | Desk lamp       | Home        | 1        | 23.75      |
| 5    | Mug             | Home        | 2        | 6.40       |
| 6    | Gift card       | Gift card   | 1        | 20.00      |

## Rules (apply in this order)

1. **Line net** = quantity x unit price.
2. **Books promotion.** If the sum of the line nets of all Books lines is at least 50.00,
   every Books line net is reduced by 10%. Each reduced line net is rounded to the nearest
   cent; an exact half cent is rounded **up**.
3. **VAT** is computed separately for each line on its (possibly reduced) line net, and each
   line's VAT is rounded to the nearest cent, exact half cents rounded **up**. Rates:
   Books 4%, Electronics 22%, Home 22%, Gift card 0% (no VAT).
4. **Shipping** is free if the sum of the (possibly reduced) line nets of all lines **except
   gift cards** is at least 100.00. Otherwise shipping costs 6.90 plus 22% VAT on those
   6.90 (VAT rounded as in rule 3).
5. **Order total** = sum of all line nets after rule 2 (gift card included) + sum of all
   line VAT + shipping including its VAT.

**Question:** what is the order total, expressed in euro cents as an integer
(for example 12.34 euros would be `1234`)?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form (an integer, no currency sign, no separators):

```
ANSWER: <value>
```
