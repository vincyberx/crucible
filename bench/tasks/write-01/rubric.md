# Rubric: write-01 (release notes)

Each criterion is pass/fail and checkable from the text of `ANSWER.md`.

1. The first line is exactly `# tidepool 4.2.0 - 2026-11-03`.
2. The only `##` headings are `## Security`, `## Breaking changes`, `## Added`, `## Fixed`,
   all four present, in this order, with no other headings below the title.
3. The set of PR numbers mentioned is exactly {#812, #815, #823, #825, #826, #834, #835, #836},
   each appearing exactly once. In particular #816, #820, #821, #827, #829, #831, #832 and
   #838 do not appear (chore/internal/test/docs, the reverted Parquet export and its fix,
   and the fix to the --dry-run flag introduced in this same release).
4. Placement: #825 and #836 are under Security; #826 is under Breaking changes (and nowhere
   else); #812 and #835 are under Added; #815, #823 and #834 are under Fixed.
5. Every bullet line ends with `(#NNN)`.
6. `CVE-2026-41877` appears in the #825 bullet and `CVE-2026-30112` appears in the #836 bullet.
7. The #826 bullet tells users what to do: it mentions migrating/converting the
   configuration to TOML.
8. The words "Falcon" and "Parquet" do not appear, no 7-character hexadecimal commit hash
   appears, and the file has at most 140 whitespace-separated tokens.
