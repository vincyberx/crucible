# Crucible · final check

Options {{LABELS}} are answers to the same task. Compare them blind and rank them. You do not know where they come from; do not try to guess.

## Read

- The task: {{TASK}}
- The acceptance checks: {{CHECKS}}

{{OPTIONS}}

## How to rank

First the checks (verify each one yourself), correctness and the absence of flaws; then clarity. Prefer the shorter option only when they are otherwise equal.

## Output

Write `{{OUT}}` as JSON and nothing else:

```json
{"ranking": ["B", "A"], "reasons": "two or three sentences on what separates them"}
```

Then reply with exactly: DONE {{JOB}}
