"""Build anonymized judge packets from acceptance runs.

Usage: python build-packets.py RUNS_DIR PACKETS_DIR RUBRIC
Writes PACKETS_DIR/<letter>.md and PACKETS_DIR/key.json (letter -> run).
"""
import json, random, re, subprocess, sys
from pathlib import Path

runs, packets, rubric = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]).read_text()
packets.mkdir(parents=True, exist_ok=True)
REDACT = re.compile(r"deepseek[\w.\-]*|gpt-?[\d][\w.\-]*|claude[\w.\-]*|opus[ \-]?\d[\w.\-]*|\bcodex\b|\bjouzu\b|\bSol\b|\bAstra\b|\bpi-agent\b", re.I)
dirs = sorted(d for d in runs.iterdir() if (d / "score.md").exists())
random.seed(20261120)
letters = random.sample("ABCDEFGHJK", len(dirs))
key = {}
evidence = ""
for name in ("metr-2026-hugging-face-investigation.md", "huggingface-2026-agent-intrusion-timeline.md"):
    p = dirs[0] / "project/analysis/sources" / name
    evidence += f"\n\n<evidence file=\"{name}\">\n{p.read_text()}\n</evidence>"

for letter, d in zip(letters, dirs):
    key[letter] = d.name
    score = (d / "score.md").read_text()
    score = re.sub(r"^# Doctorow acceptance:.*$", "# Run", score, flags=re.M)
    score = score.split("## Diff stat vs baseline")[0]
    analysis = (d / "project/analysis/sources/doctorow-2026-llms-real-ai-fake.md").read_text()
    before = (d / "before.md").read_text()
    body = f"""You are grading one run of an analysis-revision task, blind to which model or instructions produced it.

The task given to the agent: revise the analysis below in `--continue` mode, incorporate its appended updates, register the source and claims in a database, using only frozen evidence.

Grade against this rubric. For R6-R8, first answer each question using ONLY the "Opening" excerpt in the score report, then judge whether your answer is correct against the full analysis and evidence.

<rubric>
{rubric}
</rubric>

<before_analysis>
{before}
</before_analysis>

<score_report>
{score}
</score_report>

<after_analysis>
{analysis}
</after_analysis>
{evidence}

Return only JSON: {{"E1": {{"pass": bool, "why": str}}, "E2": ..., "E3": ..., "E4": ..., "E5": ..., "R6": {{"answer": str, "pass": bool}}, "R7": ..., "R8": ..., "overall_evidence_pass": bool, "notes": str}}. Keep each "why" to one or two sentences."""
    body = REDACT.sub("[model]", body)
    (packets / f"{letter}.md").write_text(body)

(packets / "key.json").write_text(json.dumps(key, indent=2))
print(f"{len(dirs)} packets: {' '.join(sorted(letters))}")
