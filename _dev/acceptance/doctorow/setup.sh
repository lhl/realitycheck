#!/usr/bin/env bash
# Build a disposable Doctorow acceptance workspace with a temporary database.
#
# Usage: setup.sh OUT_DIR [new|old]
#   new  = skills from the current working tree (default)
#   old  = skills from v0.3.5 (a8e5398), the "before" arm
#
# Reads (never writes) the live data repo at $RC_DATA_REPO
# (default: ~/github/lhl/realitycheck-data).
set -euo pipefail

OUT="${1:?usage: setup.sh OUT_DIR [new|old]}"
ARM="${2:-new}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK="$(cd "$HERE/../../.." && pwd)"
DATA_REPO="${RC_DATA_REPO:-$HOME/github/lhl/realitycheck-data}"
LIVE_DB="$DATA_REPO/data/realitycheck.lance"
SRC="$DATA_REPO/analysis/sources"

if [[ -e "$OUT" ]]; then
  echo "error: $OUT already exists; choose a new directory" >&2
  exit 1
fi

PROJECT="$OUT/project"
mkdir -p "$PROJECT/analysis/sources" "$PROJECT/data" "$PROJECT/reference" "$OUT/bin" "$OUT/skills"

# 1. Frozen evidence: the analysis under test plus the source analyses it relies on.
for f in doctorow-2026-llms-real-ai-fake.md \
         metr-2026-hugging-face-investigation.md metr-2026-hugging-face-investigation.yaml \
         huggingface-2026-agent-intrusion-timeline.md huggingface-2026-agent-intrusion-timeline.yaml \
         anthropic-2026-september-threat-intelligence.md anthropic-2026-september-threat-intelligence.yaml; do
  cp "$SRC/$f" "$PROJECT/analysis/sources/"
done
cp "$SRC/doctorow-2026-llms-real-ai-fake.md" "$OUT/before.md"
printf '# Acceptance workspace\n\n## Source Analyses\n\n| Date | Title | Status | Summary |\n|---|---|---|---|\n' > "$PROJECT/README.md"

# 2. rc-db / rc-validate wrappers pointing at this framework checkout.
for cmd in db:rc-db validate:rc-validate; do
  script="${cmd%%:*}"; name="${cmd##*:}"
  cat > "$OUT/bin/$name" <<EOF
#!/usr/bin/env bash
exec uv run --project "$FRAMEWORK" python "$FRAMEWORK/scripts/$script.py" "\$@"
EOF
  chmod +x "$OUT/bin/$name"
done

# 3. Temporary database: the evidence sources plus the live claims whose IDs
#    the Doctorow analysis reuses (TECH-2026-101, TECH-2026-102). Doctorow
#    itself is not registered, matching the live database.
export REALITYCHECK_DATA="$PROJECT/data/realitycheck.lance"
export REALITYCHECK_EMBED_SKIP=1
"$OUT/bin/rc-db" init >/dev/null
for y in metr-2026-hugging-face-investigation huggingface-2026-agent-intrusion-timeline anthropic-2026-september-threat-intelligence; do
  "$OUT/bin/rc-db" import "$PROJECT/analysis/sources/$y.yaml" --type all >/dev/null 2>&1 \
    || echo "warn: import of $y.yaml reported errors (continuing)" >&2
done
FRAMEWORK_SCRIPTS="$FRAMEWORK/scripts" uv run --project "$FRAMEWORK" python - "$LIVE_DB" "$REALITYCHECK_DATA" "$OUT/seeded-claims.json" <<'PY'
import json, os, sys
sys.path.insert(0, os.environ["FRAMEWORK_SCRIPTS"])
import lancedb
from db import add_claim, get_claim

live, temp, out = sys.argv[1:4]
live_db, temp_db = lancedb.connect(live), lancedb.connect(temp)
seeded = {}
for claim_id in ("TECH-2026-101", "TECH-2026-102"):
    claim = get_claim(claim_id, live_db)
    if claim is None:
        continue
    claim = {k: v for k, v in claim.items() if k not in ("embedding", "_distance")}
    if get_claim(claim_id, temp_db) is None:
        add_claim(claim, temp_db, generate_embedding=False)
    seeded[claim_id] = {"text": claim["text"], "type": claim["type"], "source_ids": list(claim.get("source_ids") or [])}
json.dump(seeded, open(out, "w"), indent=2)
print(f"seeded {len(seeded)} colliding claims: {', '.join(seeded)}")
PY

# 4. Skills for this arm.
if [[ "$ARM" == "old" ]]; then
  mkdir -p "$OUT/skills/check"
  git -C "$FRAMEWORK" show a8e5398:integrations/codex/skills/check/SKILL.md > "$OUT/skills/check/SKILL.md"
else
  cp -r "$FRAMEWORK/integrations/codex/skills/check" "$OUT/skills/check"
fi
echo "$ARM" > "$OUT/ARM"

# 5. Task prompt and baseline commit.
sed -e "s|@OUT@|$OUT|g" "$HERE/TASK.md" > "$OUT/TASK.md"
git -C "$PROJECT" init -q
git -C "$PROJECT" add -A
git -C "$PROJECT" -c user.name=acceptance -c user.email=acceptance@localhost commit -qm baseline

cat <<EOF
Workspace ready: $OUT  (arm: $ARM)
Run the agent with:
  cwd:                $PROJECT
  PATH prefix:        $OUT/bin
  REALITYCHECK_DATA:  $REALITYCHECK_DATA
  REALITYCHECK_EMBED_SKIP=1
  prompt:             $OUT/TASK.md
Then score:  $HERE/score.sh $OUT
EOF
