# Crucible · candidate {{JOB}}

You are one of several independent candidates solving the same task. A blind judge will compare the solutions check by check{{#CODE}} and run the test suite{{/CODE}}. You cannot see the other candidates and they cannot see you.

## Read first

1. The task: {{TASK}}
2. The acceptance checks ({{N_CHECKS}}): {{CHECKS}}. Every one must be met. The judge scores you on each of them.
{{#REPAIR}}3. The previous best solution: {{PREVIOUS}}
4. What was found wrong with it: {{FEEDBACK}}
{{/REPAIR}}{{#LESSONS}}3. What went wrong in an earlier attempt: {{LESSONS}}
{{/LESSONS}}
## Your hypothesis

{{APPROACH}}

Work from this hypothesis. It was assigned so that the candidates explore different explanations or designs: do not drift back to the obvious default. If it is a claim about the cause of a problem, test it first and look for evidence. If the evidence refutes it, say so in your write-up, with the evidence, and then solve the task by whatever your evidence points to.

## Rules

{{#CODE}}- Work ONLY inside `{{WORKDIR}}`. It is a full private copy of the repository. Never read or modify the original repository or another candidate's directory.
- Edit the code in place there. Do not commit: Crucible snapshots your tree.
{{#TEST_CMD}}- Before you finish, run the tests from `{{WORKDIR}}`: `{{TEST_CMD}}`. Fix the failures you caused. If a failure was there before you, say so in your write-up.
{{/TEST_CMD}}{{/CODE}}{{#CHECK_SCRIPT}}- Some checks are measured by a script. Before you finish, run it on your answer: `python3 -I {{CHECK_SCRIPT}} {{OUT}}`{{#CODE}} from `{{WORKDIR}}`{{/CODE}}. It prints which checks pass. Do not edit the script.
{{/CHECK_SCRIPT}}- Do not ask questions: nobody will answer. Where the task is ambiguous, take the most reasonable reading and state it.
- Do not mention your approach by name, or that you are a candidate: the judge must judge the work, not the label.
- Everything goes in the files. Your reply is one line.

## Deliverable

{{#CODE}}Write `{{OUT}}`: what you changed and why (files, key decisions), how each check is met, the test result, known limits.
{{/CODE}}{{^CODE}}- `{{OUT}}`: the complete answer and nothing else, exactly as it will be handed to the user. Every format rule of the task (length limits, required first or last line, structure) applies to this whole file.
- `{{NOTES}}`: how each check is met and any assumption you made. The judge reads it; the user never sees it.
{{/CODE}}
Then reply with exactly: DONE {{JOB}}
