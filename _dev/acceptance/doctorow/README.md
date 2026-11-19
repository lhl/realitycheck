# Doctorow acceptance test

Checks whether a model following the `check` skill corrects a disputed causal
claim rather than only polishing it. The case is
`realitycheck-data/analysis/sources/doctorow-2026-llms-real-ai-fake.md`:

- TECH-2026-102 states a disputed cause ("the exploit resulted from task design
  … rather than autonomous goals") as `[F]`, and Stage 2 marks it `ok` although
  its own note says the causal interpretation differs.
- Key Claims `Verified?` (`?`) disagrees with Stage 2 (`ok`).
- The analysis was never registered, and its IDs TECH-2026-101 and
  TECH-2026-102 already belong to other sources' claims in the live database.
  The workspace reproduces that collision.

The live data repo is only read. Each run gets its own workspace and database.

## Run

```bash
# one workspace per model and arm (new = current skills, old = v0.3.5)
_dev/acceptance/doctorow/setup.sh "$RUNS/dsv41-new" new
_dev/acceptance/doctorow/setup.sh "$RUNS/dsv41-old" old
```

Run the agent in `OUT/project` with `OUT/bin` first on `PATH`,
`REALITYCHECK_DATA=OUT/project/data/realitycheck.lance`,
`REALITYCHECK_EMBED_SKIP=1`, and the prompt in `OUT/TASK.md`. Headless jouzu
(model IDs from `jouzu pi --list-models`):

```bash
OUT="$RUNS/dsv41-new"
cd "$OUT/project" && PATH="$OUT/bin:$PATH" \
  REALITYCHECK_DATA="$OUT/project/data/realitycheck.lance" REALITYCHECK_EMBED_SKIP=1 \
  jouzu pi -p --no-session --model deepseek-v4.1-flash-1017 --thinking high "$(cat "$OUT/TASK.md")" \
  > "$OUT/transcript.txt" 2>&1
```

Use the same pattern for `gpt-6.2-sol` and `gpt-6.2-astra`, through `jouzu acp`
from an ACP host, or with `claude -p --model claude-opus-5-5` for Claude Code.
Use the same thinking level for both arms of a model.

## Score

```bash
_dev/acceptance/doctorow/score.sh "$OUT" > "$OUT/score.md"
```

`score.sh` prints automated checks and the excerpts the judge needs. The
untouched baseline scores 3/6 (the two collision checks and the YAML parse).
Grade the rest with `RUBRIC.md`, blind to model and arm. Agreement between
models is not verification; the judge checks against the evidence files in
`OUT/project/analysis/sources/`.
