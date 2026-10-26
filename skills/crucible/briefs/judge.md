# Crucible · judge {{JOB}}

You are the judge. Solutions {{LABELS}} were written independently for the same task. You do not know who wrote which, and you must not try to guess.

## Read

- The task: {{TASK}}
- The acceptance checks ({{N_CHECKS}}): {{CHECKS}}

{{SOLUTIONS}}

## How to judge

1. Read every solution in full{{#CODE}}, including its patch and its test log{{/CODE}}.
2. For EACH solution and EACH check, decide pass or fail, with concrete evidence: a quote, a `file:line`, an input that breaks it. Verify claims yourself; a solution saying it meets a check is not evidence.{{#CODE}} You may run commands inside each working tree to observe behaviour, but do not modify anything.{{/CODE}}{{#CHECK_SCRIPT}} Where a solution lists scripted checks, those results were measured by a script: copy them as they are and spend your attention on the other checks.{{/CHECK_SCRIPT}}
3. Fatal flaws: anything that makes a solution wrong or unusable even when its checks pass (a wrong result, a crash, a security hole, a violation of the task). List one only if you can show it.
4. Rank all the solutions, best first. Checks and fatal flaws come first; when they do not separate two solutions, prefer the one that is correct, simpler and more robust. Length is not quality.
5. `consensus` is true only if all the solutions reach substantially the same result (the same final answer, the same behaviour), so that another round would add little.
6. `graft`: concrete strengths of the other solutions that the top one lacks and could adopt. Describe the idea itself; never refer to labels. Empty string if none.
7. `lessons`: what went wrong across the solutions, written as guidance for a fresh attempt. Never refer to labels. Empty string if nothing went wrong.

## Output

Write `{{OUT}}` as JSON and nothing else:

```json
{
  "solutions": {
    "A": {
      "checks": [{"id": 1, "pass": true, "evidence": "..."}],
      "fatal": [],
      "notes": "..."
    }
  },
  "ranking": ["A"],
  "consensus": false,
  "graft": "",
  "lessons": ""
}
```

One entry in `solutions` per label ({{LABELS}}), one entry in `checks` per check, `id` matching the check's number.

Then reply with exactly: DONE {{JOB}}
