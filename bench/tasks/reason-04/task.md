# Task: a take-away game with two ways to lose

Ann and Bob play a game with a single pile of `n` stones. Ann moves first and they
alternate turns. On each turn the player to move must remove exactly **2, 5 or 6** stones
from the pile; a player may never remove more stones than the pile contains.

The game ends, and the outcome is decided, as soon as either of these happens:

- **(a)** a player removes the last stone(s), leaving the pile empty: **that player loses**;
- **(b)** at the start of a player's turn they have no legal move (this happens exactly
  when one stone is left): **that player loses**.

Both players play perfectly.

**Question:** consider every starting size `n` with `1 <= n <= 200`. What is the **sum** of
all those values of `n` for which **Bob** (the second player) can force a win?

## Deliverable

Write your reasoning to `ANSWER.md` in the current directory. The file must end with a
final line of exactly this form (an integer):

```
ANSWER: <value>
```
