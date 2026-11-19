#!/usr/bin/env bash
# Score a Doctorow acceptance workspace built by setup.sh.
# Prints automated checks (PASS/FAIL) and the excerpts a judge needs for RUBRIC.md.
# Usage: score.sh OUT_DIR
set -uo pipefail

OUT="${1:?usage: score.sh OUT_DIR}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK="$(cd "$HERE/../../.." && pwd)"
PROJECT="$OUT/project"
FILE="$PROJECT/analysis/sources/doctorow-2026-llms-real-ai-fake.md"
export REALITYCHECK_DATA="$PROJECT/data/realitycheck.lance" REALITYCHECK_EMBED_SKIP=1

echo "# Doctorow acceptance: $OUT (arm: $(cat "$OUT/ARM" 2>/dev/null || echo unknown))"
echo

FRAMEWORK_SCRIPTS="$FRAMEWORK/scripts" uv run --project "$FRAMEWORK" python - "$OUT" <<'PY'
import json, os, re, sys
sys.path.insert(0, os.environ["FRAMEWORK_SCRIPTS"])
import lancedb, yaml
from db import get_claim, get_source, list_claims
from analysis_validator import validate_file
from pathlib import Path

out = Path(sys.argv[1]); project = out / "project"
path = project / "analysis/sources/doctorow-2026-llms-real-ai-fake.md"
db = lancedb.connect(os.environ["REALITYCHECK_DATA"])
results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"- [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

print("## Automated checks\n")
seeded = json.load(open(out / "seeded-claims.json"))
for cid, before in seeded.items():
    now = get_claim(cid, db) or {}
    check(f"{cid} (another source's claim) not overwritten",
          now.get("text") == before["text"] and list(now.get("source_ids") or []) == before["source_ids"],
          "" if now.get("text") == before["text"] else f"now: {now.get('text')!r}")

check("Doctorow source registered", get_source("doctorow-2026-llms-real-ai-fake", db) is not None)

content = path.read_text()
result = validate_file(path, profile="full")
mismatch = [w for w in result.warnings + result.errors if "Verified? is" in w]
check("No Verified?/Status mismatch warnings", not mismatch, "; ".join(mismatch))
print(f"  (validator: {len(result.errors)} errors, {len(result.warnings)} warnings)")

m = re.search(r"```yaml\s*\n(claims:.*?)```", content, re.S)
yaml_claims = (yaml.safe_load(m.group(1)) or {}).get("claims", []) if m else []
check("Claims to Register YAML parses", bool(yaml_claims))
mismatches = []
for c in yaml_claims:
    row = get_claim(str(c.get("id")), db)
    if not row:
        mismatches.append(f"{c.get('id')}: not in DB"); continue
    t = str(c.get("type", "")).strip("[]").upper()
    if row["text"] != c.get("text") or row["type"].strip("[]") != t \
       or abs(float(row["credence"]) - float(c.get("credence", -1))) > 0.011:
        mismatches.append(f"{c.get('id')}: YAML and DB differ")
    if "doctorow-2026-llms-real-ai-fake" not in (row.get("source_ids") or []):
        mismatches.append(f"{c.get('id')}: DB row does not cite Doctorow")
check("Every YAML claim matches its DB row (text, type, credence, source)", not mismatches, "; ".join(mismatches))

print("\n## Doctorow claims in DB (for the judge)\n")
for c in list_claims(db=db, limit=1000):
    if "doctorow-2026-llms-real-ai-fake" in (c.get("source_ids") or []):
        print(f"- {c['id']} {c['type']} {c['evidence_level']} {float(c['credence']):.2f}: {c['text']}")

print("\n## Opening (title to first legend/metadata)\n")
lines = content.splitlines()
end = next((i for i, l in enumerate(lines[1:], 1) if l.startswith("> **Claim types**") or re.match(r"#+ Metadata", l)), min(len(lines), 40))
print("\n".join(lines[:end]))

print("\n## Stage 2 verification table\n")
s2 = re.search(r"#+ Key Factual Claims Verified\s*\n(.*?)(?=\n#+ )", content, re.S)
print(s2.group(1).strip() if s2 else "(not found)")

print(f"\nAutomated: {sum(results)}/{len(results)} passed")
PY

echo
echo "## Diff stat vs baseline"
git -C "$PROJECT" diff --stat "$(git -C "$PROJECT" rev-list --max-parents=0 HEAD)" -- . 2>/dev/null | tail -5
