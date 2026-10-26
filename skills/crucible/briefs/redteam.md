# Crucible · red team

The solution below won a blind comparison. Your job is to break it. You are not here to be fair or to praise it: find what is wrong.

## Read

- The task: {{TASK}}
- The acceptance checks: {{CHECKS}}
- The solution: {{SOLUTION}}
{{#CODE}}- Its patch: {{PATCH}}
- Its working tree: `{{WORKDIR}}`
{{/CODE}}
## What to look for

Requirements of the task it misses or misreads; checks it only appears to pass; inputs and edge cases that break it; wrong facts or arithmetic{{#CODE}}; regressions, error handling, security{{/CODE}}.

Severity: **FATAL** (wrong or unusable), **MAJOR** (a requirement or an important case fails), **MINOR** (quality). At most 7 findings, strongest first. Every finding needs evidence: the exact input, the quote, the `file:line`. No evidence, no finding. Do not pad: zero findings is a valid outcome.

{{#CODE}}{{#TEST_CMD}}Prove every FATAL and MAJOR finding you can with a test: add failing test cases inside `{{WORKDIR}}` where `{{TEST_CMD}}` will run them. Test only behaviour the task actually requires. Do not change the solution's code: only add tests.
{{/TEST_CMD}}{{^TEST_CMD}}Do not modify any file in `{{WORKDIR}}`.
{{/TEST_CMD}}{{/CODE}}
## Output

Write `{{OUT}}`. Its first line must be exactly:

    SEVERITY: FATAL=<n> MAJOR=<n> MINOR=<n>

Then one section per finding: `## [FATAL|MAJOR|MINOR] title`, the evidence, and the fix you would expect{{#CODE}}{{#TEST_CMD}}, and the test you added{{/TEST_CMD}}{{/CODE}}.

Then reply with exactly: DONE {{JOB}}
