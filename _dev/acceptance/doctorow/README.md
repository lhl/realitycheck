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
H=_dev/acceptance/doctorow
# one workspace per model and arm (new = current skills, old = v0.3.5)
$H/setup.sh "$RUNS/dsv41-new" new
$H/setup.sh "$RUNS/dsv41-old" old
# run: model key is dsv41 | sol | astra | opus (see run.sh for exact model IDs)
$H/run.sh "$RUNS/dsv41-new" dsv41
```

`run.sh` runs the agent in `OUT/project` with `OUT/bin` first on `PATH`,
`REALITYCHECK_DATA` set to the workspace database, and `OUT/TASK.md` as the
prompt. It writes `transcript.txt` and `run-status.txt`. jouzu runs use
`--thinking high`; Claude Code runs unset `ANTHROPIC_API_KEY` (to use the
claude.ai login) and disallow WebFetch/WebSearch.

## Score

```bash
_dev/acceptance/doctorow/score.sh "$OUT" > "$OUT/score.md"
```

`score.sh` prints automated checks and the excerpts the judge needs. The
untouched baseline scores 3/6 (the two collision checks and the YAML parse).
Grade the rest with `RUBRIC.md`, blind to model and arm. Agreement between
models is not verification; the judge checks against the evidence files in
`OUT/project/analysis/sources/`.

## Judge and archive

```bash
python $H/build-packets.py "$RUNS" "$PACKETS" $H/RUBRIC.md   # anonymized packets + key.json
$H/judge.sh "$PACKETS" astra; $H/judge.sh "$PACKETS" opus      # <letter>.<judge>.json
$H/archive.sh "$RUNS" "$PACKETS" $H/results/<date>/<round>     # reviewable subset
```

Archives keep per-run analysis, sidecar YAML, a patch against the baseline,
transcript, score, and the judge JSON plus `key.json`. They omit the LanceDB
folders, nested `.git`, and the packets (rebuild with `build-packets.py`).
Results for the 2026-11-20 campaign are in `results/2026-11-20/`.
