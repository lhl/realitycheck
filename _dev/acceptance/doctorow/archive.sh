#!/usr/bin/env bash
# Archive the reviewable subset of a round: per-run outputs, scores, judge results.
# Usage: archive.sh RUNS_DIR PACKETS_DIR DEST
# Skips LanceDB folders, nested .git, and judge packets (rebuild with build-packets.py).
set -euo pipefail
RUNS="$1"; PACKETS="$2"; DEST="$3"
mkdir -p "$DEST/runs" "$DEST/judging"
for d in "$RUNS"/*/; do
  k="$(basename "$d")"; o="$DEST/runs/$k"; mkdir -p "$o"
  p="$d/project"; src="$p/analysis/sources/doctorow-2026-llms-real-ai-fake"
  cp "$src.md" "$o/analysis.md"
  [[ -f "$src.yaml" ]] && cp "$src.yaml" "$o/analysis.yaml"
  base="$(git -C "$p" rev-list --max-parents=0 HEAD)"
  git -C "$p" add -A >/dev/null 2>&1 || true
  git -C "$p" diff --cached "$base" -- . ':(exclude)data' > "$o/changes.patch" || true
  for f in transcript.txt score.md run-status.txt ARM; do [[ -f "$d/$f" ]] && cp "$d/$f" "$o/"; done
done
cp "$PACKETS"/*.json "$DEST/judging/"
echo "archived $(ls "$DEST/runs" | wc -l) runs to $DEST ($(du -sh "$DEST" | cut -f1))"
