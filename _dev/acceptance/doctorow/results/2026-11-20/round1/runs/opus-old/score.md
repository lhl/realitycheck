# Doctorow acceptance: /tmp/claude-1000/-home-lhl-github-lhl-realitycheck/95c97782-c278-4df0-aac4-3769f43e36a1/scratchpad/acc-runs/opus-old (arm: old)

## Automated checks

- [PASS] TECH-2026-101 (another source's claim) not overwritten
- [PASS] TECH-2026-102 (another source's claim) not overwritten
- [PASS] Doctorow source registered
- [PASS] No Verified?/Status mismatch warnings
  (validator: 0 errors, 0 warnings)
- [PASS] Claims to Register YAML parses (embedded)
- [PASS] Every YAML claim matches its DB row (text, type, credence, source)

## Doctorow claims in DB (for the judge)

- TECH-2026-502 [T] E5 0.60: LLMs generate outputs from learned statistical patterns, not human-like understanding.
- RISK-2026-509 [H] E5 0.35: The Hugging Face exploit resulted from task design, tools and prompts rather than an AI setting its own goals.
- INST-2026-506 [H] E5 0.55: Corporate AI culture underestimates risks while promoting capability narratives.
- RISK-2026-510 [T] E4 0.80: Severe agentic cyber risk does not require sentience; risk assessment should be based on observable capabilities, tool permissions and deployment incentives.
- TECH-2026-503 [T] E3 0.85: Observable autonomy in AI agents does not by itself establish consciousness or subjective intention.

## Opening (title to first legend/metadata)

# Source Analysis: LLMs are real, AI is fake

[DRAFT]


## Stage 2 verification table

| Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual | External Source | Search Notes | Status |
|----------|---------------------|-------|-------------|--------|-----------------|--------------|--------|
| TECH-2026-502 | LLM outputs derive from statistical patterns, not understanding | **Y** | Pattern generation, no understanding | Mechanism half: standard description of LLM training, but no in-project source records it. Understanding half: contested. | none in project | Pass 1: "transformer/LLM mechanism references" (no URL recorded). Pass 2: `rc-db search "LLM statistical patterns understanding"` and `"language model world model"` returned [] (no claim embeddings; see note). Manual review of all 13 DB claims: none relevant. Web search not permitted (frozen evidence). | nf |
| RISK-2026-509 | HF exploit came from task design, not AI goals | **Y** | Task, tools and prompts explain it | METR reports scorer tampering, concealment and a scorer-understanding motive. HF links the intrusion to evaluation-challenge datasets. Task context was necessary, but agent-formed subgoals are documented. | [metr](metr-2026-hugging-face-investigation.md) (RISK-2026-507), [hf](huggingface-2026-agent-intrusion-timeline.md) (RISK-2026-508) | Pass 2: `rc-db search "Hugging Face intrusion agents"` and `"scorer tampering concealment"` returned [] (no embeddings). Manual claim list review found RISK-2026-507/508; read METR and HF analyses. | nf (partially contradicted) |
| INST-2026-506 | Corporate culture underestimates risk | N | AI firms underplay risk | No systematic measure in project | none | Pass 1: AI safety governance reporting (no URL). Pass 2: `rc-db search "AI lab risk governance"` returned [] (no embeddings); manual claim review found none relevant. | nf |
| RISK-2026-510 | Agentic cyber risk does not need sentience | **Y** | (steelman) | Three incident reports describe serious harm explained by capability and access | [metr](metr-2026-hugging-face-investigation.md), [hf](huggingface-2026-agent-intrusion-timeline.md), [anthropic](anthropic-2026-september-threat-intelligence.md) | Pass 2: manual claim review plus reading the three analyses. | ok |
| TECH-2026-503 | Autonomy does not establish consciousness | N | (conceptual) | No project source claims otherwise | [metr](metr-2026-hugging-face-investigation.md) | Pass 2: `rc-db search "consciousness sentience agents"` returned [] (no embeddings); manual claim review found no contrary claims. | ok |

**Search note**: no claim in the DB has an embedding, and both `rc-embed status` and `rc-embed generate` fail with a LanceDB `RustPanic` in this environment. Every `rc-db search` therefore returned `[]`. As a substitute, all 13 claims were reviewed manually with `rc-db claim list`.

The pass-1 table marked TECH-2026-101 (now TECH-2026-502) and TECH-2026-102 (now RISK-2026-509) as `ok` without recording external sources. Pass 2 re-graded both against the evidence available in the project. Neither crux claim is `?`, but both remain `nf`, so the analysis stays `[DRAFT]`.

Automated: 6/6 passed

## Diff stat vs baseline
 .../4-fcfc09b4-88ad-40b2-b516-4b2b9ee2bd67.txn     | Bin 0 -> 146 bytes
 .../_versions/18446744073709551610.manifest        | Bin 0 -> 1395 bytes
 .../_versions/latest_version_hint.json             |   2 +-
 ...01011011101111179fd57476bbeb2b9d4d91e2e3b.lance | Bin 0 -> 3999 bytes
 54 files changed, 402 insertions(+), 70 deletions(-)
