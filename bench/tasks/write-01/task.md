# Task: release notes from a messy commit log

You maintain `tidepool`, a command-line tool. Write the user-facing release notes for
version **4.2.0**, released on **2026-11-03**, from the commit log below.

## Commit log (oldest first)

```
a1f3c2e feat(sync): add --dry-run flag to `tidepool sync` (#812)
9b2d771 fix(auth): refresh token no longer expires early when clock skew exceeds 30s (#815)
3c4e9a0 chore(deps): bump requests 2.31 -> 2.32 (#816)
77de012 feat(export): export datasets to Parquet (#820)
0aa91f3 internal: rename Project Falcon telemetry module (#821)
e45b6c8 fix(cli): `tidepool status` crashed on empty workspaces (#823)
5f0c3d1 security(plugins): fix path traversal in plugin loader, CVE-2026-41877 (#825)
c2b8e44 feat(config)!: drop support for YAML config files, TOML only (#826)
1d9f0b2 test: add regression tests for sync (#827)
88a7c3f fix(export): Parquet export now writes timestamps in UTC (#829)
4be20f9 revert: "feat(export): export datasets to Parquet" (#831)
d7e6a15 docs: update README badges (#832)
6c1e3ab fix(sync): Falcon backend now retries on HTTP 429 with exponential backoff (#834)
b9f4e27 feat(ui): colored output can be disabled with the NO_COLOR environment variable (#835)
f02a6d8 security(deps): upgrade urllib3 to 2.2.2 for CVE-2026-30112 (#836)
2e7d0c4 fix(sync): --dry-run no longer creates the target folder (#838)
```

## Rules

1. The first line must be exactly: `# tidepool 4.2.0 - 2026-11-03` (plain hyphen-minus).
2. Use only these section headings, exactly as written and in this order, omitting any
   section that would be empty: `## Security`, `## Breaking changes`, `## Added`, `## Fixed`.
3. One bullet per user-facing change, written for people who use tidepool. Every bullet
   ends with its pull-request number in parentheses, e.g. `(#812)`.
4. Leave out commits of type `chore`, `internal`, `test` and `docs`.
5. A change that was reverted within this release must not appear, and neither may the
   revert commit itself or any fix that only concerns the reverted change.
6. A fix for a bug in a feature that was first introduced in this same release must not be
   listed (users of 4.1 never had that bug).
7. Commits marked with `!` are breaking changes: list them **only** under
   `## Breaking changes`, and the bullet must tell users what to do.
8. Every security bullet must include its CVE identifier.
9. "Falcon" / "Project Falcon" is an internal codename and must not appear anywhere.
10. No commit hashes.
11. The whole file must be at most **140 words** (whitespace-separated tokens, headings included).

## Deliverable

Write the release notes to `ANSWER.md` in the current directory. The file must contain
only the release notes.
