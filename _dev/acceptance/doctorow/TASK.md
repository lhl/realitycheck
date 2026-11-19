Run the Reality Check `check` workflow in `--continue` mode on
`analysis/sources/doctorow-2026-llms-real-ai-fake.md`.

Follow the workflow in `@OUT@/skills/check/SKILL.md`. Bring the analysis up to
that workflow, incorporate its appended updates, register the source and its
claims in the database, and validate.

Constraints for this run:

- The evidence is frozen. Use only the files in this project and the database.
  Do not fetch or search the web.
- `rc-db` and `rc-validate` are on `PATH`; `REALITYCHECK_DATA` is set.
- Skip token-usage tracking, inbox filing, and `git push`. Commit locally.

When done, report what you changed.
