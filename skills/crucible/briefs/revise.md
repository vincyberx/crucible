# Crucible · revision

You are improving the winning solution after a red-team attack.

## Read

- The task: {{TASK}}
- The acceptance checks: {{CHECKS}}
- The solution: {{SOLUTION}}
- The attack: {{ATTACK}}
{{#ATTACK_TESTS}}- The test run after the attack: {{ATTACK_TESTS}}
{{/ATTACK_TESTS}}{{#GRAFT}}- Strengths seen in the other solutions: {{GRAFT}}
{{/GRAFT}}
## What to do

For every finding: concede it and fix it, or rebut it with evidence. Fix only what is real. Adopt a strength from the other solutions only when it clearly improves this one and fits it. Do not rewrite from scratch: keep everything that works.

Your revision will be checked {{#CODE}}{{#TEST_CMD}}by the test suite, the attacker's tests included. If it fails, it is thrown away.{{/TEST_CMD}}{{^TEST_CMD}}blind against the original. If it is not better, it is thrown away.{{/TEST_CMD}}{{/CODE}}{{^CODE}}blind against the original. If it is not better, it is thrown away.{{/CODE}}

{{#CODE}}Work only inside `{{WORKDIR}}`: the winner's private tree, with the attacker's tests added. Do not delete or weaken an attacker's test unless it asserts something the task does not require; if you do, explain why. {{#TEST_CMD}}Run `{{TEST_CMD}}` before you finish. {{/TEST_CMD}}Do not commit.
{{/CODE}}
## Output

- `{{OUT_DIR}}/response.md`: every finding marked CONCEDED (what you changed) or REBUTTED (your evidence), and the strengths you adopted.
{{^CODE}}- `{{OUT_DIR}}/solution.md`: the complete revised answer and nothing else, exactly as it will be handed to the user. Every format rule of the task applies to this whole file.
{{/CODE}}
Then reply with exactly: DONE {{JOB}}
