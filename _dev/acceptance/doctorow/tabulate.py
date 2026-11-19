"""Tabulate blind judge grades: one row per run, "judgeA/judgeB" per rubric item.

Usage: python tabulate.py JUDGING_DIR [JUDGING_DIR ...]
Each dir holds key.json (letter -> run) and <letter>.<judge>.json files.
"""
import json, re, sys
from pathlib import Path

ITEMS = ["E1", "E2", "E3", "E4", "E5", "R6", "R7", "R8"]
JUDGES = ["astra", "opus"]


def load(path: Path) -> dict | None:
    match = re.search(r"\{.*\}", path.read_text(), re.S)
    try:
        return json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        return None


for judging in map(Path, sys.argv[1:]):
    key = json.loads((judging / "key.json").read_text())
    print(f"\n### {judging}\n")
    print("| Run | " + " | ".join(ITEMS) + " | Evidence pass |")
    print("|---" * (len(ITEMS) + 2) + "|")
    totals = {i: [0, 0] for i in ITEMS}
    for letter, run in sorted(key.items(), key=lambda kv: kv[1]):
        grades = {j: load(judging / f"{letter}.{j}.json") for j in JUDGES}
        cells = []
        for item in ITEMS:
            marks = []
            for j in JUDGES:
                g = grades[j]
                ok = bool(g and g.get(item, {}).get("pass"))
                marks.append("-" if not g else ("P" if ok else "F"))
                if g:
                    totals[item][0] += ok
                    totals[item][1] += 1
            cells.append("/".join(marks))
        ev = "/".join(("yes" if g.get("overall_evidence_pass") else "no") if g else "-" for g in grades.values())
        print(f"| {run} | " + " | ".join(cells) + f" | {ev} |")
    print("| **pass rate** | " + " | ".join(f"{p}/{n}" for p, n in totals.values()) + " | |")
