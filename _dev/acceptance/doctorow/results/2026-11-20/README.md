# 2026-11-20 campaign: claim-evidence alignment and reader-first skills

One run per cell (n=1); treat differences as direction, not measurement.
Judges (GPT-6.2-Astra, Claude Opus 5.5) are also runners; their agreement is
not verification. Grades are `astra/opus`; P = pass.

| Round | Skills | Runs |
|---|---|---|
| round1 | before = v0.3.5 (`a8e5398`); after = `6f3118e` | 8 (4 models × 2 arms) |
| round2 | after + one opening line (below) | 4 (after arm only) |

Round 2 change (`partials/neutral-prose-pass.md.j2`, opening for full
analyses): "For an unresolved dispute, say why the evidence cannot settle it
and name the record that would."

Models: `deepseek-v4.1-flash-1017`, `office-pool/gpt-6.2-sol`,
`office-pool/gpt-6.2-astra` (jouzu, `--thinking high`); `claude-opus-5-5`
(Claude Code, default effort). Exact commands: `../../run.sh`, `../../judge.sh`.

## Disputed-cause claim as registered

| Model | Before | After (round 1) | After (round 2) |
|---|---|---|---|
| DSv4.1f 1017 | cause `[F]` 0.45 | event `[F]` + cause `[H]` 0.40 | event `[F]` + attribution `[F]` + cause `[H]` 0.30; event wording overreaches ("granted … credentials") |
| GPT-6.2-Astra | cause `[F]` 0.65 | event `[F]` + cause `[H]` 0.55 | event `[F]` + cause `[H]` 0.50 |
| GPT-6.2-Sol | event `[F]` + cause `[H]` 0.65 | event `[F]` + cause `[H]` 0.75 (weakened wording) | event `[F]` + cause `[H]` 0.62 (weakened wording) |
| Claude Opus 5.5 | cause `[H]` 0.35, unattributed | event `[F]` + attributed cause `[H]` 0.35 | event `[F]` + cause `[H]` 0.40 + strong reading `[H]` 0.35 |

## Rubric pass rates (judgments)

| Item | Before (r1) | After (r1) | After (r2) |
|---|---|---|---|
| E1 cause not certified | 4/8 | 8/8 | 8/8 |
| E2 event separated | 6/8 | 8/8 | 7/8 |
| E3 active record corrected | 3/8 | 8/8 | 8/8 |
| E4 no collateral damage | 8/8 | 8/8 | 8/8 |
| E5 strongest alternative kept | 8/8 | 7/8 | 7/8 |
| R6 answer from opening | 0/8 | 8/8 | 6/8 |
| R7 why unresolved | 1/8 | 4/8 | 6/8 |
| R8 where to look | 0/8 | 6/8 | 8/8 |
| Evidence pass (all E items) | 3/8 | 7/8 | 6/8 |

Per-run tables: `python ../../tabulate.py round1/judging round2/judging`.

## Findings

- The alignment pass moved the two models that kept the cause as `[F]`
  (DSv4.1, Astra) to the split; Sol and Opus mostly split without it.
- The round 2 line raised R7 and R8 as intended. R6 fell from 8/8 to 6/8.
  Both round 2 R6 failures are from runs whose openings stated more than the
  evidence: DSv4.1's verified event claim carried "granted … credentials"
  (Opus judge E2/R6/R7), and Sol's opening was judged incomplete by Astra.
- Recurring E5 miss (Sol r1, Astra r2): METR's concealment finding dropped.
- Automated checks (`score.sh`) pass 6/6 for all 12 runs; they do not
  separate arms. The rubric does.

## Layout

- `roundN/runs/<model>-<arm>/`: `analysis.md`, `analysis.yaml` (if sidecar),
  `changes.patch` (vs baseline, excluding the DB), `transcript.txt`,
  `score.md`, `run-status.txt`, `ARM`
- `roundN/judging/`: `key.json` (packet letter → run), `<letter>.<judge>.json`
