# Reality Check - Development Statistics by Tagged Release

*Generated (UTC): `2026-02-17T16:53:51.951108+00:00`*
*Repo: `/home/lhl/github/lhl/realitycheck`*
*Tag count in report: `15`*

## Methodology

- Git churn is computed from each release range (`prev_tag..tag`, first tag uses full history to tag).
- Session usage is summed from local JSONL logs scoped to this repo path:
  - Codex: `~/.codex/sessions/**/rollout-*.jsonl` (windowed counter deltas).
  - Claude: `~/.claude/projects/-home-lhl-github-lhl-realitycheck/*.jsonl` (per-message usage sums).
- Active/coding/planning times are estimates from timestamp bursts:
  - `active`: contiguous event clusters (gap <= 5m).
  - `coding`: tool-use/function-call clusters.
  - `planning`: `active - coding`.
- Cost assumptions used for estimated USD:
  - Codex/gpt-5.x: uncached input `$1.250` / cached input `$0.125` / output `$10.00` per 1M.
  - Claude/Opus-4.x: base input `$15.00` / cache write `$18.75` / cache read `$1.50` / output `$75.00` per 1M.
- `scc` snapshots are taken from `git archive <tag>` extracts when `--with-scc` is enabled.

## Project Totals

| Provider   |         Input |    Output |         Total |   Est Cost (USD) |
|:-----------|--------------:|----------:|--------------:|-----------------:|
| Codex      |   672,925,975 | 4,322,700 |   677,248,675 |          $146.33 |
| Claude     |   703,983,876 |    23,392 |   704,007,268 |        $1,672.40 |
| Combined   | 1,376,909,851 | 4,346,092 | 1,381,255,943 |        $1,818.74 |

| Cache-Sensitive Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:----------------------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x                     |            16,880,791 |    656,045,184 |             - |            - |
| Claude/Opus-4.x                   |               601,835 |              - |    35,161,906 |  668,220,135 |

| Activity             |   Duration |   Seconds |
|:---------------------|-----------:|----------:|
| Active (estimated)   | 1d 19h 23m |   156,207 |
| Coding (estimated)   | 1d 15h 17m |   141,475 |
| Planning (estimated) |      4h 5m |    14,732 |

| Test Composition (sum across tags)   |   Value |
|:-------------------------------------|--------:|
| Test files                           |     166 |
| Test functions                       |   3,726 |
| Unit functions                       |   3,552 |
| Integration functions                |     174 |
| Adversarial functions                |       0 |

| Documentation Churn (sum across tags)   |   Value |
|:----------------------------------------|--------:|
| Commits touching docs scope             |     129 |
| Unique doc files touched                |     123 |
| Insertions                              |  19,713 |
| Deletions                               |   2,972 |
| Net lines                               |  16,741 |

## Summary Table

| Tag            | Tag Commit (UTC)            | Prev Tag       |    Cadence |   Work Span |   Commits |   Files |      + |     - |    Net |   Codex Tokens |   Claude Tokens |   Est Cost (USD) |   Active (est) |   Coding (est) |   Planning (est) |   Tests |   Doc Net |   Python LOC (scc) |
|:---------------|:----------------------------|:---------------|-----------:|------------:|----------:|--------:|-------:|------:|-------:|---------------:|----------------:|-----------------:|---------------:|---------------:|-----------------:|--------:|----------:|-------------------:|
| `v0.1.0-alpha` | `2026-01-20T14:43:13+00:00` | `-`            |          - |      3h 55m |         8 |      39 |  8,639 |   211 |  8,428 |      6,447,862 |      48,518,118 |          $120.61 |         1h 15m |         1h 15m |               0m |     108 |     3,093 |              3,459 |
| `v0.1.0-beta`  | `2026-01-20T16:00:01+00:00` | `v0.1.0-alpha` |     1h 16m |      1h 16m |         4 |      27 |  3,884 |   700 |  3,184 |      5,925,761 |      49,266,331 |          $115.32 |         1h 16m |         1h 16m |               0m |     129 |       897 |              4,870 |
| `v0.1.0`       | `2026-01-21T07:06:42+00:00` | `v0.1.0-beta`  |     15h 6m |      8h 51m |        27 |      78 |  5,413 | 1,407 |  4,006 |     62,028,418 |     150,551,244 |          $332.15 |         5h 46m |          5h 1m |              44m |     137 |     1,232 |              6,073 |
| `v0.1.1`       | `2026-01-21T08:59:18+00:00` | `v0.1.0`       |     1h 52m |      1h 51m |        22 |      54 |  1,632 |   896 |    736 |     25,737,727 |      61,436,562 |          $146.01 |         1h 41m |         1h 38m |               2m |     142 |       318 |              6,375 |
| `v0.1.2`       | `2026-01-21T09:19:42+00:00` | `v0.1.1`       |        20m |          6m |         3 |       5 |     46 |     1 |     45 |      4,266,300 |       8,653,899 |           $18.69 |            20m |            20m |               0m |     142 |        25 |              6,375 |
| `v0.1.3`       | `2026-01-22T02:13:29+00:00` | `v0.1.2`       |    16h 53m |     16h 45m |        16 |      84 |  9,110 | 1,116 |  7,994 |     49,104,253 |      56,195,149 |          $144.93 |         3h 36m |         3h 22m |              13m |     196 |     1,759 |              7,883 |
| `v0.1.4`       | `2026-01-24T19:19:04+00:00` | `v0.1.3`       |  2d 17h 5m |  2d 16h 24m |        31 |      70 |  7,480 |   953 |  6,527 |    157,063,354 |      57,237,291 |          $206.91 |         8h 41m |         7h 49m |              51m |     248 |     1,847 |             11,217 |
| `v0.1.5`       | `2026-01-25T17:47:38+00:00` | `v0.1.4`       |    22h 28m |     12h 16m |        22 |      33 |  3,803 |   288 |  3,515 |     74,958,729 |      81,626,761 |          $213.06 |          4h 7m |         3h 45m |              22m |     272 |     1,599 |             12,367 |
| `v0.1.6`       | `2026-01-25T17:49:52+00:00` | `v0.1.5`       |         2m |          0m |         1 |       3 |      6 |     2 |      4 |              0 |       2,574,726 |            $4.09 |             2m |             2m |               0m |     272 |         4 |             12,367 |
| `v0.1.7`       | `2026-01-26T05:26:14+00:00` | `v0.1.6`       |    11h 36m |          3m |         2 |       9 |    388 |    93 |    295 |              0 |      10,632,255 |           $32.20 |            39m |            29m |               9m |     294 |        14 |             12,581 |
| `v0.1.8`       | `2026-01-26T07:32:39+00:00` | `v0.1.7`       |      2h 6m |          3m |         2 |      20 |    471 |     6 |    465 |     14,992,625 |       9,383,165 |           $31.73 |          1h 8m |             1h |               7m |     294 |        78 |             12,581 |
| `v0.1.9`       | `2026-01-27T19:50:15+00:00` | `v0.1.8`       | 1d 12h 17m |   1d 9h 23m |         3 |      23 |  2,819 |     9 |  2,810 |     60,527,323 |       4,346,933 |           $26.86 |         3h 21m |         2h 47m |              34m |     294 |       946 |             12,581 |
| `v0.2.0`       | `2026-01-30T19:11:23+00:00` | `v0.1.9`       | 2d 23h 21m |      1d 42m |         6 |      28 |  5,458 |   474 |  4,984 |     13,315,698 |      84,786,750 |          $191.00 |         2h 13m |         1h 59m |              14m |     385 |       982 |             15,785 |
| `v0.3.0`       | `2026-02-01T04:55:59+00:00` | `v0.2.0`       |  1d 9h 44m |   1d 9h 25m |        13 |      35 |  3,415 |   397 |  3,018 |    116,920,125 |      78,306,110 |          $218.12 |          6h 3m |         5h 44m |              18m |     401 |     1,561 |             16,667 |
| `v0.3.1`       | `2026-02-11T09:51:02+00:00` | `v0.3.0`       | 10d 4h 55m |  10d 3h 29m |         9 |      24 |  3,981 |    49 |  3,932 |     85,960,500 |         491,974 |           $17.06 |          3h 9m |         2h 44m |              25m |     412 |     2,386 |             18,030 |
| **TOTAL**      | -                           | -              |          - |           - |       169 |     532 | 56,545 | 6,602 | 49,943 |    677,248,675 |     704,007,268 |        $1,818.74 |     1d 19h 23m |     1d 15h 17m |            4h 5m |   3,726 |    16,741 |                  - |

## v0.1.0-alpha

- Tag commit: `68bacb6` (`2026-01-20T14:43:13+00:00`)
- Previous tag: `-`
- Cadence since previous tag: `-`
- Git range: `v0.1.0-alpha`
- Range commit span: `2026-01-20T10:48:03+00:00` -> `2026-01-20T14:43:13+00:00`
- Range work duration: `3h 55m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       8 |
| Unique files touched      |      39 |
| Insertions                |   8,639 |
| Deletions                 |     211 |
| Net lines                 |   8,428 |
| Cumulative commits at tag |       8 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                      - |
| Work span in range         |                 3h 55m |
| Commits/day (inclusive)    |                    8.0 |
| Commits/hour (active span) |                   2.04 |
| Peak commit day            | 2026-01-20 (8 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-20 |         8 |

- Usage window: `START` -> `2026-01-20T14:43:13+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 1 sessions / 1 files |  6,392,276 |   55,586 |  6,447,862 |            $1.72 |
| Claude         | 4 files              | 48,516,892 |    1,226 | 48,518,118 |          $118.89 |
| Combined       | -                    | 54,909,168 |   56,812 | 54,965,980 |          $120.61 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               325,588 |      6,066,688 |             - |            - |
| Claude/Opus-4.x        |                70,571 |              - |     2,612,639 |   45,833,682 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |      812 | 3h 39m |      25m |      21m |         4m | 3h 14m |         0.1155 |
| Claude                 |      567 | 3h 51m |    1h 9m |    1h 8m |         0m | 2h 42m |         0.2996 |
| Combined               |    1,379 | 3h 39m |   1h 15m |   1h 15m |         0m | 2h 23m |         0.3456 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       4 |          97 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |       5 |         108 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       7 |
| Unique files touched        |      12 |
| Insertions                  |   3,236 |
| Deletions                   |     143 |
| Net lines                   |   3,093 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |      36 |
| Total code lines            |   6,310 |
| Python files                |      13 |
| Python code lines           |   3,459 |
| COCOMO estimated cost (USD) | 186,907 |
| COCOMO schedule (months)    |    7.27 |
| COCOMO people               |    2.28 |

## v0.1.0-beta

- Tag commit: `1aa82ec` (`2026-01-20T16:00:01+00:00`)
- Previous tag: `v0.1.0-alpha`
- Cadence since previous tag: `1h 16m`
- Git range: `v0.1.0-alpha..v0.1.0-beta`
- Range commit span: `2026-01-20T14:43:29+00:00` -> `2026-01-20T16:00:01+00:00`
- Range work duration: `1h 16m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       4 |
| Unique files touched      |      27 |
| Insertions                |   3,884 |
| Deletions                 |     700 |
| Net lines                 |   3,184 |
| Cumulative commits at tag |      12 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                 1h 16m |
| Work span in range         |                 1h 16m |
| Commits/day (inclusive)    |                    4.0 |
| Commits/hour (active span) |                   3.14 |
| Peak commit day            | 2026-01-20 (2 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-20 |         2 |
| 2026-01-21 |         2 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |   Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|--------:|----------:|
| Commits                           |          8 |          4 |      -4 |    -50.0% |
| Net lines                         |      8,428 |      3,184 |  -5,244 |    -62.2% |
| Combined tokens                   | 54,965,980 | 55,192,092 | 226,112 |     +0.4% |
| Estimated cost (USD)              |    $120.61 |    $115.32 |  $-5.29 |     -4.4% |
| Test functions                    |        108 |        129 |      21 |    +19.4% |

- Usage window: `2026-01-20T14:43:13+00:00` -> `2026-01-20T16:00:01+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 1 sessions / 1 files |  5,870,249 |   55,512 |  5,925,761 |            $1.48 |
| Claude         | 6 files              | 49,265,056 |    1,275 | 49,266,331 |          $113.84 |
| Combined       | -                    | 55,135,305 |   56,787 | 55,192,092 |          $115.32 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               169,513 |      5,700,736 |             - |            - |
| Claude/Opus-4.x        |                54,194 |              - |     2,267,821 |   46,943,041 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |      722 | 1h 16m |      25m |      22m |         2m |    50m |         0.3362 |
| Claude                 |      522 | 1h 16m |    1h 1m |    1h 1m |         0m |    14m |         0.8066 |
| Combined               |    1,244 | 1h 16m |   1h 16m |   1h 16m |         0m |     0m |         0.9989 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       4 |         118 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |       5 |         129 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       4 |
| Unique files touched        |       9 |
| Insertions                  |   1,554 |
| Deletions                   |     657 |
| Net lines                   |     897 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |      49 |
| Total code lines            |   8,860 |
| Python files                |      13 |
| Python code lines           |   4,870 |
| COCOMO estimated cost (USD) | 266,932 |
| COCOMO schedule (months)    |    8.33 |
| COCOMO people               |    2.85 |

## v0.1.0

- Tag commit: `1ccb505` (`2026-01-21T07:06:42+00:00`)
- Previous tag: `v0.1.0-beta`
- Cadence since previous tag: `15h 6m`
- Git range: `v0.1.0-beta..v0.1.0`
- Range commit span: `2026-01-20T22:14:45+00:00` -> `2026-01-21T07:06:42+00:00`
- Range work duration: `8h 51m`
- Inclusive day span: `2`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      27 |
| Unique files touched      |      78 |
| Insertions                |   5,413 |
| Deletions                 |   1,407 |
| Net lines                 |   4,006 |
| Cumulative commits at tag |      39 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |                  15h 6m |
| Work span in range         |                  8h 51m |
| Commits/day (inclusive)    |                    13.5 |
| Commits/hour (active span) |                    3.05 |
| Peak commit day            | 2026-01-21 (27 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-21 |        27 |

| Release Snapshot Delta vs Prior   |   Previous |     Current |       Delta |   Delta % |
|:----------------------------------|-----------:|------------:|------------:|----------:|
| Commits                           |          4 |          27 |          23 |   +575.0% |
| Net lines                         |      3,184 |       4,006 |         822 |    +25.8% |
| Combined tokens                   | 55,192,092 | 212,579,662 | 157,387,570 |   +285.2% |
| Estimated cost (USD)              |    $115.32 |     $332.15 |     $216.83 |   +188.0% |
| Test functions                    |        129 |         137 |           8 |     +6.2% |

- Usage window: `2026-01-20T16:00:01+00:00` -> `2026-01-21T07:06:42+00:00`

| Usage Source   | Files/Sessions       |       Input |   Output |       Total |   Est Cost (USD) |
|:---------------|:---------------------|------------:|---------:|------------:|-----------------:|
| Codex          | 1 sessions / 1 files |  61,592,654 |  435,764 |  62,028,418 |           $13.64 |
| Claude         | 10 files             | 150,546,135 |    5,109 | 150,551,244 |          $318.51 |
| Combined       | -                    | 212,138,789 |  440,873 | 212,579,662 |          $332.15 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             1,405,262 |     60,187,392 |             - |            - |
| Claude/Opus-4.x        |                75,746 |              - |     5,291,794 |  145,178,595 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |    Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|--------:|---------------:|
| Codex                  |    5,190 | 15h 6m |   3h 58m |    3h 7m |        51m |  11h 7m |         0.2635 |
| Claude                 |    1,730 | 15h 6m |   3h 28m |   3h 15m |        13m | 11h 38m |           0.23 |
| Combined               |    6,920 | 15h 6m |   5h 46m |    5h 1m |        44m |  9h 20m |         0.3816 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       5 |         126 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |       6 |         137 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |      18 |
| Unique files touched        |      14 |
| Insertions                  |   1,645 |
| Deletions                   |     413 |
| Net lines                   |   1,232 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |      70 |
| Total code lines            |  11,927 |
| Python files                |      15 |
| Python code lines           |   6,073 |
| COCOMO estimated cost (USD) | 364,714 |
| COCOMO schedule (months)    |    9.37 |
| COCOMO people               |    3.46 |

## v0.1.1

- Tag commit: `ed9be9c` (`2026-01-21T08:59:18+00:00`)
- Previous tag: `v0.1.0`
- Cadence since previous tag: `1h 52m`
- Git range: `v0.1.0..v0.1.1`
- Range commit span: `2026-01-21T07:07:34+00:00` -> `2026-01-21T08:59:18+00:00`
- Range work duration: `1h 51m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      22 |
| Unique files touched      |      54 |
| Insertions                |   1,632 |
| Deletions                 |     896 |
| Net lines                 |     736 |
| Cumulative commits at tag |      61 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |                  1h 52m |
| Work span in range         |                  1h 51m |
| Commits/day (inclusive)    |                    22.0 |
| Commits/hour (active span) |                   11.81 |
| Peak commit day            | 2026-01-21 (22 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-21 |        22 |

| Release Snapshot Delta vs Prior   |    Previous |    Current |        Delta |   Delta % |
|:----------------------------------|------------:|-----------:|-------------:|----------:|
| Commits                           |          27 |         22 |           -5 |    -18.5% |
| Net lines                         |       4,006 |        736 |       -3,270 |    -81.6% |
| Combined tokens                   | 212,579,662 | 87,174,289 | -125,405,373 |    -59.0% |
| Estimated cost (USD)              |     $332.15 |    $146.01 |     $-186.14 |    -56.0% |
| Test functions                    |         137 |        142 |            5 |     +3.6% |

- Usage window: `2026-01-21T07:06:42+00:00` -> `2026-01-21T08:59:18+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 3 sessions / 3 files | 25,542,272 |  195,455 | 25,737,727 |            $5.72 |
| Claude         | 3 files              | 61,435,108 |    1,454 | 61,436,562 |          $140.30 |
| Combined       | -                    | 86,977,380 |  196,909 | 87,174,289 |          $146.01 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               505,600 |     25,036,672 |             - |            - |
| Claude/Opus-4.x        |                33,646 |              - |     2,758,338 |   58,643,124 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |    2,513 | 1h 52m |   1h 23m |   1h 16m |         6m |    29m |         0.7395 |
| Claude                 |      581 | 1h 52m |      57m |      52m |         4m |    55m |         0.5075 |
| Combined               |    3,094 | 1h 52m |   1h 41m |   1h 38m |         2m |    11m |          0.897 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       7 |         131 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |       8 |         142 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |      13 |
| Unique files touched        |       9 |
| Insertions                  |     589 |
| Deletions                   |     271 |
| Net lines                   |     318 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |      75 |
| Total code lines            |  12,471 |
| Python files                |      18 |
| Python code lines           |   6,375 |
| COCOMO estimated cost (USD) | 382,200 |
| COCOMO schedule (months)    |    9.54 |
| COCOMO people               |    3.56 |

## v0.1.2

- Tag commit: `349a176` (`2026-01-21T09:19:42+00:00`)
- Previous tag: `v0.1.1`
- Cadence since previous tag: `20m`
- Git range: `v0.1.1..v0.1.2`
- Range commit span: `2026-01-21T09:13:39+00:00` -> `2026-01-21T09:19:42+00:00`
- Range work duration: `6m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       3 |
| Unique files touched      |       5 |
| Insertions                |      46 |
| Deletions                 |       1 |
| Net lines                 |      45 |
| Cumulative commits at tag |      64 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                    20m |
| Work span in range         |                     6m |
| Commits/day (inclusive)    |                    3.0 |
| Commits/hour (active span) |                  29.75 |
| Peak commit day            | 2026-01-21 (3 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-21 |         3 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |       Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|------------:|----------:|
| Commits                           |         22 |          3 |         -19 |    -86.4% |
| Net lines                         |        736 |         45 |        -691 |    -93.9% |
| Combined tokens                   | 87,174,289 | 12,920,199 | -74,254,090 |    -85.2% |
| Estimated cost (USD)              |    $146.01 |     $18.69 |    $-127.32 |    -87.2% |
| Test functions                    |        142 |        142 |           0 |     +0.0% |

- Usage window: `2026-01-21T08:59:18+00:00` -> `2026-01-21T09:19:42+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 2 sessions / 2 files |  4,211,677 |   54,623 |  4,266,300 |            $1.31 |
| Claude         | 1 files              |  8,653,722 |      177 |  8,653,899 |           $17.38 |
| Combined       | -                    | 12,865,399 |   54,800 | 12,920,199 |           $18.69 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               210,397 |      4,001,280 |             - |            - |
| Claude/Opus-4.x        |                 4,778 |              - |       250,578 |    8,398,366 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |      666 |    20m |      17m |      16m |         0m |     3m |         0.8407 |
| Claude                 |       66 |    20m |      20m |      20m |         0m |     0m |         0.9984 |
| Combined               |      732 |    20m |      20m |      20m |         0m |     0m |         0.9992 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       7 |         131 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |       8 |         142 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       2 |
| Unique files touched        |       1 |
| Insertions                  |      25 |
| Deletions                   |       0 |
| Net lines                   |      25 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |      75 |
| Total code lines            |  12,496 |
| Python files                |      18 |
| Python code lines           |   6,375 |
| COCOMO estimated cost (USD) | 383,005 |
| COCOMO schedule (months)    |    9.55 |
| COCOMO people               |    3.56 |

## v0.1.3

- Tag commit: `8993b73` (`2026-01-22T02:13:29+00:00`)
- Previous tag: `v0.1.2`
- Cadence since previous tag: `16h 53m`
- Git range: `v0.1.2..v0.1.3`
- Range commit span: `2026-01-21T09:28:00+00:00` -> `2026-01-22T02:13:29+00:00`
- Range work duration: `16h 45m`
- Inclusive day span: `2`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      16 |
| Unique files touched      |      84 |
| Insertions                |   9,110 |
| Deletions                 |   1,116 |
| Net lines                 |   7,994 |
| Cumulative commits at tag |      80 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |                 16h 53m |
| Work span in range         |                 16h 45m |
| Commits/day (inclusive)    |                     8.0 |
| Commits/hour (active span) |                    0.95 |
| Peak commit day            | 2026-01-22 (15 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-21 |         1 |
| 2026-01-22 |        15 |

| Release Snapshot Delta vs Prior   |   Previous |     Current |      Delta |   Delta % |
|:----------------------------------|-----------:|------------:|-----------:|----------:|
| Commits                           |          3 |          16 |         13 |   +433.3% |
| Net lines                         |         45 |       7,994 |      7,949 | +17664.4% |
| Combined tokens                   | 12,920,199 | 105,299,402 | 92,379,203 |   +715.0% |
| Estimated cost (USD)              |     $18.69 |     $144.93 |    $126.24 |   +675.4% |
| Test functions                    |        142 |         196 |         54 |    +38.0% |

- Usage window: `2026-01-21T09:19:42+00:00` -> `2026-01-22T02:13:29+00:00`

| Usage Source   | Files/Sessions       |       Input |   Output |       Total |   Est Cost (USD) |
|:---------------|:---------------------|------------:|---------:|------------:|-----------------:|
| Codex          | 5 sessions / 5 files |  48,705,177 |  399,076 |  49,104,253 |           $11.38 |
| Claude         | 3 files              |  56,193,871 |    1,278 |  56,195,149 |          $133.55 |
| Combined       | -                    | 104,899,048 |  400,354 | 105,299,402 |          $144.93 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             1,156,121 |     47,549,056 |             - |            - |
| Claude/Opus-4.x        |                38,304 |              - |     2,819,891 |   53,335,676 |

| Activity (estimated)   |   Events |    Wall |   Active |   Coding |   Planning |    Idle |   Active Ratio |
|:-----------------------|---------:|--------:|---------:|---------:|-----------:|--------:|---------------:|
| Codex                  |    4,668 | 16h 53m |   2h 56m |   2h 31m |        25m | 13h 57m |         0.1741 |
| Claude                 |      597 | 16h 53m |   1h 14m |    1h 8m |         6m | 15h 39m |         0.0731 |
| Combined               |    5,265 | 16h 53m |   3h 36m |   3h 22m |        13m | 13h 17m |         0.2131 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |       9 |         185 |
| Integration        |       1 |          11 |
| Adversarial        |       0 |           0 |
| Total              |      10 |         196 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |      12 |
| Unique files touched        |      10 |
| Insertions                  |   2,224 |
| Deletions                   |     465 |
| Net lines                   |   1,759 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     132 |
| Total code lines            |  18,444 |
| Python files                |      23 |
| Python code lines           |   7,883 |
| COCOMO estimated cost (USD) | 576,425 |
| COCOMO schedule (months)    |   11.16 |
| COCOMO people               |    4.59 |

## v0.1.4

- Tag commit: `37df792` (`2026-01-24T19:19:04+00:00`)
- Previous tag: `v0.1.3`
- Cadence since previous tag: `2d 17h 5m`
- Git range: `v0.1.3..v0.1.4`
- Range commit span: `2026-01-22T02:54:39+00:00` -> `2026-01-24T19:19:04+00:00`
- Range work duration: `2d 16h 24m`
- Inclusive day span: `3`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      31 |
| Unique files touched      |      70 |
| Insertions                |   7,480 |
| Deletions                 |     953 |
| Net lines                 |   6,527 |
| Cumulative commits at tag |     111 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |               2d 17h 5m |
| Work span in range         |              2d 16h 24m |
| Commits/day (inclusive)    |                   10.33 |
| Commits/hour (active span) |                    0.48 |
| Peak commit day            | 2026-01-24 (14 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-22 |         9 |
| 2026-01-23 |         5 |
| 2026-01-24 |        14 |
| 2026-01-25 |         3 |

| Release Snapshot Delta vs Prior   |    Previous |     Current |       Delta |   Delta % |
|:----------------------------------|------------:|------------:|------------:|----------:|
| Commits                           |          16 |          31 |          15 |    +93.8% |
| Net lines                         |       7,994 |       6,527 |      -1,467 |    -18.4% |
| Combined tokens                   | 105,299,402 | 214,300,645 | 109,001,243 |   +103.5% |
| Estimated cost (USD)              |     $144.93 |     $206.91 |      $61.98 |    +42.8% |
| Test functions                    |         196 |         248 |          52 |    +26.5% |

- Usage window: `2026-01-22T02:13:29+00:00` -> `2026-01-24T19:19:04+00:00`

| Usage Source   | Files/Sessions         |       Input |    Output |       Total |   Est Cost (USD) |
|:---------------|:-----------------------|------------:|----------:|------------:|-----------------:|
| Codex          | 13 sessions / 13 files | 155,953,514 | 1,109,840 | 157,063,354 |           $35.70 |
| Claude         | 8 files                |  57,232,086 |     5,205 |  57,237,291 |          $171.21 |
| Combined       | -                      | 213,185,600 | 1,115,045 | 214,300,645 |          $206.91 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             4,537,706 |    151,415,808 |             - |            - |
| Claude/Opus-4.x        |                11,781 |              - |     4,916,532 |   52,303,773 |

| Activity (estimated)   |   Events |      Wall |   Active |   Coding |   Planning |       Idle |   Active Ratio |
|:-----------------------|---------:|----------:|---------:|---------:|-----------:|-----------:|---------------:|
| Codex                  |   13,612 | 2d 17h 5m |   7h 21m |   6h 29m |        51m |  2d 9h 44m |          0.113 |
| Claude                 |      653 | 2d 17h 5m |   1h 35m |   1h 26m |         9m | 2d 15h 30m |         0.0244 |
| Combined               |   14,265 | 2d 17h 5m |   8h 41m |   7h 49m |        51m |  2d 8h 24m |         0.1334 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      12 |         236 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      13 |         248 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |      27 |
| Unique files touched        |      17 |
| Insertions                  |   2,050 |
| Deletions                   |     203 |
| Net lines                   |   1,847 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     152 |
| Total code lines            |  23,947 |
| Python files                |      28 |
| Python code lines           |  11,217 |
| COCOMO estimated cost (USD) | 758,244 |
| COCOMO schedule (months)    |   12.38 |
| COCOMO people               |    5.44 |

## v0.1.5

- Tag commit: `8045813` (`2026-01-25T17:47:38+00:00`)
- Previous tag: `v0.1.4`
- Cadence since previous tag: `22h 28m`
- Git range: `v0.1.4..v0.1.5`
- Range commit span: `2026-01-25T05:31:24+00:00` -> `2026-01-25T17:47:38+00:00`
- Range work duration: `12h 16m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      22 |
| Unique files touched      |      33 |
| Insertions                |   3,803 |
| Deletions                 |     288 |
| Net lines                 |   3,515 |
| Cumulative commits at tag |     133 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |                 22h 28m |
| Work span in range         |                 12h 16m |
| Commits/day (inclusive)    |                    22.0 |
| Commits/hour (active span) |                    1.79 |
| Peak commit day            | 2026-01-25 (16 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-25 |        16 |
| 2026-01-26 |         6 |

| Release Snapshot Delta vs Prior   |    Previous |     Current |       Delta |   Delta % |
|:----------------------------------|------------:|------------:|------------:|----------:|
| Commits                           |          31 |          22 |          -9 |    -29.0% |
| Net lines                         |       6,527 |       3,515 |      -3,012 |    -46.1% |
| Combined tokens                   | 214,300,645 | 156,585,490 | -57,715,155 |    -26.9% |
| Estimated cost (USD)              |     $206.91 |     $213.06 |       $6.15 |     +3.0% |
| Test functions                    |         248 |         272 |          24 |     +9.7% |

- Usage window: `2026-01-24T19:19:04+00:00` -> `2026-01-25T17:47:38+00:00`

| Usage Source   | Files/Sessions       |       Input |   Output |       Total |   Est Cost (USD) |
|:---------------|:---------------------|------------:|---------:|------------:|-----------------:|
| Codex          | 3 sessions / 3 files |  74,478,211 |  480,518 |  74,958,729 |           $16.18 |
| Claude         | 4 files              |  81,624,612 |    2,149 |  81,626,761 |          $196.87 |
| Combined       | -                    | 156,102,823 |  482,667 | 156,585,490 |          $213.06 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             1,839,875 |     72,638,336 |             - |            - |
| Claude/Opus-4.x        |                21,575 |              - |     4,288,909 |   77,314,128 |

| Activity (estimated)   |   Events |    Wall |   Active |   Coding |   Planning |    Idle |   Active Ratio |
|:-----------------------|---------:|--------:|---------:|---------:|-----------:|--------:|---------------:|
| Codex                  |    5,966 | 22h 28m |   3h 20m |   2h 54m |        26m |  19h 7m |         0.1489 |
| Claude                 |      934 | 22h 28m |   1h 48m |   1h 33m |        15m | 20h 40m |         0.0803 |
| Combined               |    6,900 | 22h 28m |    4h 7m |   3h 45m |        22m | 18h 20m |         0.1837 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      12 |         260 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      13 |         272 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |      18 |
| Unique files touched        |      13 |
| Insertions                  |   1,770 |
| Deletions                   |     171 |
| Net lines                   |   1,599 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     157 |
| Total code lines            |  26,489 |
| Python files                |      28 |
| Python code lines           |  12,367 |
| COCOMO estimated cost (USD) | 842,973 |
| COCOMO schedule (months)    |   12.89 |
| COCOMO people               |    5.81 |

## v0.1.6

- Tag commit: `c939a72` (`2026-01-25T17:49:52+00:00`)
- Previous tag: `v0.1.5`
- Cadence since previous tag: `2m`
- Git range: `v0.1.5..v0.1.6`
- Range commit span: `2026-01-25T17:49:52+00:00` -> `2026-01-25T17:49:52+00:00`
- Range work duration: `0m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       1 |
| Unique files touched      |       3 |
| Insertions                |       6 |
| Deletions                 |       2 |
| Net lines                 |       4 |
| Cumulative commits at tag |     134 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                     2m |
| Work span in range         |                     0m |
| Commits/day (inclusive)    |                    1.0 |
| Commits/hour (active span) |                        |
| Peak commit day            | 2026-01-26 (1 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-26 |         1 |

| Release Snapshot Delta vs Prior   |    Previous |   Current |        Delta |   Delta % |
|:----------------------------------|------------:|----------:|-------------:|----------:|
| Commits                           |          22 |         1 |          -21 |    -95.5% |
| Net lines                         |       3,515 |         4 |       -3,511 |    -99.9% |
| Combined tokens                   | 156,585,490 | 2,574,726 | -154,010,764 |    -98.4% |
| Estimated cost (USD)              |     $213.06 |     $4.09 |     $-208.97 |    -98.1% |
| Test functions                    |         272 |       272 |            0 |     +0.0% |

- Usage window: `2026-01-25T17:47:38+00:00` -> `2026-01-25T17:49:52+00:00`

| Usage Source   | Files/Sessions       |     Input |   Output |     Total |   Est Cost (USD) |
|:---------------|:---------------------|----------:|---------:|----------:|-----------------:|
| Codex          | 0 sessions / 0 files |         0 |        0 |         0 |            $0.00 |
| Claude         | 1 files              | 2,574,666 |       60 | 2,574,726 |            $4.09 |
| Combined       | -                    | 2,574,666 |       60 | 2,574,726 |            $4.09 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |                     0 |              0 |             - |            - |
| Claude/Opus-4.x        |                   178 |              - |        12,857 |    2,561,631 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |        0 |     2m |       0m |       0m |         0m |     2m |              0 |
| Claude                 |       24 |     2m |       2m |       2m |         0m |     0m |         0.9627 |
| Combined               |       24 |     2m |       2m |       2m |         0m |     0m |         0.9627 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      12 |         260 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      13 |         272 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       1 |
| Unique files touched        |       2 |
| Insertions                  |       5 |
| Deletions                   |       1 |
| Net lines                   |       4 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     157 |
| Total code lines            |  26,491 |
| Python files                |      28 |
| Python code lines           |  12,367 |
| COCOMO estimated cost (USD) | 843,040 |
| COCOMO schedule (months)    |   12.89 |
| COCOMO people               |    5.81 |

## v0.1.7

- Tag commit: `3c4345b` (`2026-01-26T05:26:14+00:00`)
- Previous tag: `v0.1.6`
- Cadence since previous tag: `11h 36m`
- Git range: `v0.1.6..v0.1.7`
- Range commit span: `2026-01-26T05:23:14+00:00` -> `2026-01-26T05:26:14+00:00`
- Range work duration: `3m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       2 |
| Unique files touched      |       9 |
| Insertions                |     388 |
| Deletions                 |      93 |
| Net lines                 |     295 |
| Cumulative commits at tag |     136 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                11h 36m |
| Work span in range         |                     3m |
| Commits/day (inclusive)    |                    2.0 |
| Commits/hour (active span) |                   40.0 |
| Peak commit day            | 2026-01-26 (2 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-26 |         2 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |     Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|----------:|----------:|
| Commits                           |          1 |          2 |         1 |   +100.0% |
| Net lines                         |          4 |        295 |       291 |  +7275.0% |
| Combined tokens                   |  2,574,726 | 10,632,255 | 8,057,529 |   +312.9% |
| Estimated cost (USD)              |      $4.09 |     $32.20 |    $28.11 |   +687.3% |
| Test functions                    |        272 |        294 |        22 |     +8.1% |

- Usage window: `2026-01-25T17:49:52+00:00` -> `2026-01-26T05:26:14+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 0 sessions / 0 files |          0 |        0 |          0 |            $0.00 |
| Claude         | 7 files              | 10,631,688 |      567 | 10,632,255 |           $32.20 |
| Combined       | -                    | 10,631,688 |      567 | 10,632,255 |           $32.20 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |                     0 |              0 |             - |            - |
| Claude/Opus-4.x        |                66,561 |              - |       887,485 |    9,677,642 |

| Activity (estimated)   |   Events |    Wall |   Active |   Coding |   Planning |    Idle |   Active Ratio |
|:-----------------------|---------:|--------:|---------:|---------:|-----------:|--------:|---------------:|
| Codex                  |        0 | 11h 36m |       0m |       0m |         0m | 11h 36m |              0 |
| Claude                 |      221 | 11h 36m |      39m |      29m |         9m | 10h 56m |         0.0568 |
| Combined               |      221 | 11h 36m |      39m |      29m |         9m | 10h 56m |         0.0568 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      13 |         282 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      14 |         294 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       1 |
| Unique files touched        |       2 |
| Insertions                  |      15 |
| Deletions                   |       1 |
| Net lines                   |      14 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     158 |
| Total code lines            |  26,713 |
| Python files                |      29 |
| Python code lines           |  12,581 |
| COCOMO estimated cost (USD) | 850,460 |
| COCOMO schedule (months)    |   12.93 |
| COCOMO people               |    5.84 |

## v0.1.8

- Tag commit: `bcba834` (`2026-01-26T07:32:39+00:00`)
- Previous tag: `v0.1.7`
- Cadence since previous tag: `2h 6m`
- Git range: `v0.1.7..v0.1.8`
- Range commit span: `2026-01-26T07:29:27+00:00` -> `2026-01-26T07:32:39+00:00`
- Range work duration: `3m`
- Inclusive day span: `1`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       2 |
| Unique files touched      |      20 |
| Insertions                |     471 |
| Deletions                 |       6 |
| Net lines                 |     465 |
| Cumulative commits at tag |     138 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |                  2h 6m |
| Work span in range         |                     3m |
| Commits/day (inclusive)    |                    2.0 |
| Commits/hour (active span) |                   37.5 |
| Peak commit day            | 2026-01-26 (2 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-26 |         2 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |      Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|-----------:|----------:|
| Commits                           |          2 |          2 |          0 |     +0.0% |
| Net lines                         |        295 |        465 |        170 |    +57.6% |
| Combined tokens                   | 10,632,255 | 24,375,790 | 13,743,535 |   +129.3% |
| Estimated cost (USD)              |     $32.20 |     $31.73 |     $-0.47 |     -1.5% |
| Test functions                    |        294 |        294 |          0 |     +0.0% |

- Usage window: `2026-01-26T05:26:14+00:00` -> `2026-01-26T07:32:39+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 1 sessions / 1 files | 14,883,313 |  109,312 | 14,992,625 |            $3.47 |
| Claude         | 5 files              |  9,382,632 |      533 |  9,383,165 |           $28.26 |
| Combined       | -                    | 24,265,945 |  109,845 | 24,375,790 |           $31.73 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               456,945 |     14,426,368 |             - |            - |
| Claude/Opus-4.x        |                72,437 |              - |       763,653 |    8,546,542 |

| Activity (estimated)   |   Events |   Wall |   Active |   Coding |   Planning |   Idle |   Active Ratio |
|:-----------------------|---------:|-------:|---------:|---------:|-----------:|-------:|---------------:|
| Codex                  |    1,247 |  2h 6m |       1h |      49m |        11m |  1h 5m |         0.4809 |
| Claude                 |      157 |  2h 6m |      16m |      15m |         1m | 1h 49m |         0.1339 |
| Combined               |    1,404 |  2h 6m |    1h 8m |       1h |         7m |    57m |         0.5434 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      13 |         282 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      14 |         294 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       2 |
| Unique files touched        |       3 |
| Insertions                  |      79 |
| Deletions                   |       1 |
| Net lines                   |      78 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     158 |
| Total code lines            |  27,047 |
| Python files                |      29 |
| Python code lines           |  12,581 |
| COCOMO estimated cost (USD) | 861,629 |
| COCOMO schedule (months)    |    13.0 |
| COCOMO people               |    5.89 |

## v0.1.9

- Tag commit: `4eff4be` (`2026-01-27T19:50:15+00:00`)
- Previous tag: `v0.1.8`
- Cadence since previous tag: `1d 12h 17m`
- Git range: `v0.1.8..v0.1.9`
- Range commit span: `2026-01-26T10:26:57+00:00` -> `2026-01-27T19:50:15+00:00`
- Range work duration: `1d 9h 23m`
- Inclusive day span: `2`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       3 |
| Unique files touched      |      23 |
| Insertions                |   2,819 |
| Deletions                 |       9 |
| Net lines                 |   2,810 |
| Cumulative commits at tag |     141 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |             1d 12h 17m |
| Work span in range         |              1d 9h 23m |
| Commits/day (inclusive)    |                    1.5 |
| Commits/hour (active span) |                   0.09 |
| Peak commit day            | 2026-01-28 (2 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-26 |         1 |
| 2026-01-28 |         2 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |      Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|-----------:|----------:|
| Commits                           |          2 |          3 |          1 |    +50.0% |
| Net lines                         |        465 |      2,810 |      2,345 |   +504.3% |
| Combined tokens                   | 24,375,790 | 64,874,256 | 40,498,466 |   +166.1% |
| Estimated cost (USD)              |     $31.73 |     $26.86 |     $-4.87 |    -15.3% |
| Test functions                    |        294 |        294 |          0 |     +0.0% |

- Usage window: `2026-01-26T07:32:39+00:00` -> `2026-01-27T19:50:15+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 3 sessions / 3 files | 60,131,493 |  395,830 | 60,527,323 |           $13.08 |
| Claude         | 2 files              |  4,346,781 |      152 |  4,346,933 |           $13.77 |
| Combined       | -                    | 64,478,274 |  395,982 | 64,874,256 |           $26.86 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             1,430,053 |     58,701,440 |             - |            - |
| Claude/Opus-4.x        |                   612 |              - |       419,361 |    3,926,808 |

| Activity (estimated)   |   Events |       Wall |   Active |   Coding |   Planning |      Idle |   Active Ratio |
|:-----------------------|---------:|-----------:|---------:|---------:|-----------:|----------:|---------------:|
| Codex                  |    4,161 | 1d 12h 17m |   3h 15m |   2h 41m |        33m |  1d 9h 2m |         0.0898 |
| Claude                 |       73 | 1d 12h 17m |       8m |       6m |         1m | 1d 12h 9m |         0.0037 |
| Combined               |    4,234 | 1d 12h 17m |   3h 21m |   2h 47m |        34m | 1d 8h 55m |         0.0927 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      13 |         282 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      14 |         294 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       2 |
| Unique files touched        |       5 |
| Insertions                  |     947 |
| Deletions                   |       1 |
| Net lines                   |     946 |

| scc Snapshot                |   Value |
|:----------------------------|--------:|
| Total files                 |     174 |
| Total code lines            |  29,116 |
| Python files                |      29 |
| Python code lines           |  12,581 |
| COCOMO estimated cost (USD) | 930,965 |
| COCOMO schedule (months)    |   13.38 |
| COCOMO people               |    6.18 |

## v0.2.0

- Tag commit: `e550507` (`2026-01-30T19:11:23+00:00`)
- Previous tag: `v0.1.9`
- Cadence since previous tag: `2d 23h 21m`
- Git range: `v0.1.9..v0.2.0`
- Range commit span: `2026-01-29T18:29:20+00:00` -> `2026-01-30T19:11:23+00:00`
- Range work duration: `1d 42m`
- Inclusive day span: `2`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       6 |
| Unique files touched      |      28 |
| Insertions                |   5,458 |
| Deletions                 |     474 |
| Net lines                 |   4,984 |
| Cumulative commits at tag |     147 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |             2d 23h 21m |
| Work span in range         |                 1d 42m |
| Commits/day (inclusive)    |                    3.0 |
| Commits/hour (active span) |                   0.24 |
| Peak commit day            | 2026-01-30 (4 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-30 |         4 |
| 2026-01-31 |         2 |

| Release Snapshot Delta vs Prior   |   Previous |    Current |      Delta |   Delta % |
|:----------------------------------|-----------:|-----------:|-----------:|----------:|
| Commits                           |          3 |          6 |          3 |   +100.0% |
| Net lines                         |      2,810 |      4,984 |      2,174 |    +77.4% |
| Combined tokens                   | 64,874,256 | 98,102,448 | 33,228,192 |    +51.2% |
| Estimated cost (USD)              |     $26.86 |    $191.00 |    $164.14 |   +611.1% |
| Test functions                    |        294 |        385 |         91 |    +31.0% |

- Usage window: `2026-01-27T19:50:15+00:00` -> `2026-01-30T19:11:23+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 2 sessions / 2 files | 13,204,015 |  111,683 | 13,315,698 |            $3.24 |
| Claude         | 17 files             | 84,784,406 |    2,344 | 84,786,750 |          $187.76 |
| Combined       | -                    | 97,988,421 |  114,027 | 98,102,448 |          $191.00 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |               421,679 |     12,782,336 |             - |            - |
| Claude/Opus-4.x        |                48,307 |              - |     3,464,163 |   81,271,936 |

| Activity (estimated)   |   Events |       Wall |   Active |   Coding |   Planning |       Idle |   Active Ratio |
|:-----------------------|---------:|-----------:|---------:|---------:|-----------:|-----------:|---------------:|
| Codex                  |    1,417 | 2d 23h 21m |      58m |      41m |        16m | 2d 22h 22m |         0.0136 |
| Claude                 |      870 | 2d 23h 21m |   1h 44m |   1h 29m |        14m | 2d 21h 36m |         0.0243 |
| Combined               |    2,287 | 2d 23h 21m |   2h 13m |   1h 59m |        14m |  2d 21h 8m |         0.0311 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      13 |         373 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      14 |         385 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       6 |
| Unique files touched        |       9 |
| Insertions                  |   1,369 |
| Deletions                   |     387 |
| Net lines                   |     982 |

| scc Snapshot                |     Value |
|:----------------------------|----------:|
| Total files                 |       177 |
| Total code lines            |    33,517 |
| Python files                |        29 |
| Python code lines           |    15,785 |
| COCOMO estimated cost (USD) | 1,079,254 |
| COCOMO schedule (months)    |     14.16 |
| COCOMO people               |      6.77 |

## v0.3.0

- Tag commit: `ba60d4f` (`2026-02-01T04:55:59+00:00`)
- Previous tag: `v0.2.0`
- Cadence since previous tag: `1d 9h 44m`
- Git range: `v0.2.0..v0.3.0`
- Range commit span: `2026-01-30T19:30:23+00:00` -> `2026-02-01T04:55:59+00:00`
- Range work duration: `1d 9h 25m`
- Inclusive day span: `3`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |      13 |
| Unique files touched      |      35 |
| Insertions                |   3,415 |
| Deletions                 |     397 |
| Net lines                 |   3,018 |
| Cumulative commits at tag |     160 |

| Velocity                   |                   Value |
|:---------------------------|------------------------:|
| Cadence since previous tag |               1d 9h 44m |
| Work span in range         |               1d 9h 25m |
| Commits/day (inclusive)    |                    4.33 |
| Commits/hour (active span) |                    0.39 |
| Peak commit day            | 2026-02-01 (10 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-01-31 |         3 |
| 2026-02-01 |        10 |

| Release Snapshot Delta vs Prior   |   Previous |     Current |      Delta |   Delta % |
|:----------------------------------|-----------:|------------:|-----------:|----------:|
| Commits                           |          6 |          13 |          7 |   +116.7% |
| Net lines                         |      4,984 |       3,018 |     -1,966 |    -39.4% |
| Combined tokens                   | 98,102,448 | 195,226,235 | 97,123,787 |    +99.0% |
| Estimated cost (USD)              |    $191.00 |     $218.12 |     $27.12 |    +14.2% |
| Test functions                    |        385 |         401 |         16 |     +4.2% |

- Usage window: `2026-01-30T19:11:23+00:00` -> `2026-02-01T04:55:59+00:00`

| Usage Source   | Files/Sessions       |       Input |   Output |       Total |   Est Cost (USD) |
|:---------------|:---------------------|------------:|---------:|------------:|-----------------:|
| Codex          | 5 sessions / 5 files | 116,338,036 |  582,089 | 116,920,125 |           $23.13 |
| Claude         | 40 files             |  78,304,266 |    1,844 |  78,306,110 |          $194.99 |
| Combined       | -                    | 194,642,302 |  583,933 | 195,226,235 |          $218.12 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             2,462,196 |    113,875,840 |             - |            - |
| Claude/Opus-4.x        |               103,073 |              - |     4,405,757 |   73,795,436 |

| Activity (estimated)   |   Events |      Wall |   Active |   Coding |   Planning |      Idle |   Active Ratio |
|:-----------------------|---------:|----------:|---------:|---------:|-----------:|----------:|---------------:|
| Codex                  |    8,385 | 1d 9h 44m |   4h 34m |   4h 14m |        19m | 1d 5h 10m |         0.1355 |
| Claude                 |      806 | 1d 9h 44m |   1h 44m |   1h 38m |         6m | 1d 7h 59m |         0.0517 |
| Combined               |    9,191 | 1d 9h 44m |    6h 3m |   5h 44m |        18m | 1d 3h 41m |         0.1795 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      13 |         389 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      14 |         401 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       8 |
| Unique files touched        |       8 |
| Insertions                  |   1,787 |
| Deletions                   |     226 |
| Net lines                   |   1,561 |

| scc Snapshot                |     Value |
|:----------------------------|----------:|
| Total files                 |       179 |
| Total code lines            |    35,803 |
| Python files                |        29 |
| Python code lines           |    16,667 |
| COCOMO estimated cost (USD) | 1,156,673 |
| COCOMO schedule (months)    |     14.54 |
| COCOMO people               |      7.07 |

## v0.3.1

- Tag commit: `d6dce1d` (`2026-02-11T09:51:02+00:00`)
- Previous tag: `v0.3.0`
- Cadence since previous tag: `10d 4h 55m`
- Git range: `v0.3.0..v0.3.1`
- Range commit span: `2026-02-01T06:21:41+00:00` -> `2026-02-11T09:51:02+00:00`
- Range work duration: `10d 3h 29m`
- Inclusive day span: `11`

| Metric                    |   Value |
|:--------------------------|--------:|
| Commits in range          |       9 |
| Unique files touched      |      24 |
| Insertions                |   3,981 |
| Deletions                 |      49 |
| Net lines                 |   3,932 |
| Cumulative commits at tag |     169 |

| Velocity                   |                  Value |
|:---------------------------|-----------------------:|
| Cadence since previous tag |             10d 4h 55m |
| Work span in range         |             10d 3h 29m |
| Commits/day (inclusive)    |                   0.82 |
| Commits/hour (active span) |                   0.04 |
| Peak commit day            | 2026-02-01 (8 commits) |

| Date       |   Commits |
|:-----------|----------:|
| 2026-02-01 |         8 |
| 2026-02-11 |         1 |

| Release Snapshot Delta vs Prior   |    Previous |    Current |        Delta |   Delta % |
|:----------------------------------|------------:|-----------:|-------------:|----------:|
| Commits                           |          13 |          9 |           -4 |    -30.8% |
| Net lines                         |       3,018 |      3,932 |          914 |    +30.3% |
| Combined tokens                   | 195,226,235 | 86,452,474 | -108,773,761 |    -55.7% |
| Estimated cost (USD)              |     $218.12 |     $17.06 |     $-201.06 |    -92.2% |
| Test functions                    |         401 |        412 |           11 |     +2.7% |

- Usage window: `2026-02-01T04:55:59+00:00` -> `2026-02-11T09:51:02+00:00`

| Usage Source   | Files/Sessions       |      Input |   Output |      Total |   Est Cost (USD) |
|:---------------|:---------------------|-----------:|---------:|-----------:|-----------------:|
| Codex          | 4 sessions / 4 files | 85,623,088 |  337,412 | 85,960,500 |           $16.28 |
| Claude         | 2 files              |    491,955 |       19 |    491,974 |            $0.78 |
| Combined       | -                    | 86,115,043 |  337,431 | 86,452,474 |           $17.06 |

| Cost Input Breakdown   |   Uncached/Base Input |   Cached Input |   Cache Write |   Cache Read |
|:-----------------------|----------------------:|---------------:|--------------:|-------------:|
| Codex/gpt-5.x          |             1,959,856 |     83,663,232 |             - |            - |
| Claude/Opus-4.x        |                    72 |              - |         2,128 |      489,755 |

| Activity (estimated)   |   Events |       Wall |   Active |   Coding |   Planning |       Idle |   Active Ratio |
|:-----------------------|---------:|-----------:|---------:|---------:|-----------:|-----------:|---------------:|
| Codex                  |    5,693 | 10d 4h 55m |    3h 8m |   2h 43m |        25m | 10d 1h 46m |         0.0128 |
| Claude                 |       10 | 10d 4h 55m |       1m |       1m |         0m | 10d 4h 54m |         0.0001 |
| Combined               |    5,703 | 10d 4h 55m |    3h 9m |   2h 44m |        25m | 10d 1h 45m |         0.0129 |

| Test Composition   |   Files |   Functions |
|:-------------------|--------:|------------:|
| Unit               |      14 |         400 |
| Integration        |       1 |          12 |
| Adversarial        |       0 |           0 |
| Total              |      15 |         412 |

| Documentation Churn         |   Value |
|:----------------------------|--------:|
| Commits touching docs scope |       8 |
| Unique files touched        |       9 |
| Insertions                  |   2,418 |
| Deletions                   |      32 |
| Net lines                   |   2,386 |

| scc Snapshot                |     Value |
|:----------------------------|----------:|
| Total files                 |       183 |
| Total code lines            |    38,709 |
| Python files                |        31 |
| Python code lines           |    18,030 |
| COCOMO estimated cost (USD) | 1,255,445 |
| COCOMO schedule (months)    |      15.0 |
| COCOMO people               |      7.44 |

## Repro Commands

```bash
python scripts/release_stats_rollup.py \
  --repo-root . \
  --with-scc \
  --with-test-composition \
  --output-json /tmp/realitycheck-release-stats.json \
  --output-markdown docs/STATUS-dev-stats.md
```
