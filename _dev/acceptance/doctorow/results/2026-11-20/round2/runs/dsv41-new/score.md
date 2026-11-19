# Doctorow acceptance: /tmp/claude-1000/-home-lhl-github-lhl-realitycheck/95c97782-c278-4df0-aac4-3769f43e36a1/scratchpad/acc-runs-r2/dsv41-new (arm: new)

## Automated checks

- [PASS] TECH-2026-101 (another source's claim) not overwritten
- [PASS] TECH-2026-102 (another source's claim) not overwritten
- [PASS] Doctorow source registered
- [PASS] No Verified?/Status mismatch warnings
  (validator: 5 errors, 2 warnings)
- [PASS] Claims to Register YAML parses (sidecar .yaml)
- [PASS] Every YAML claim matches its DB row (text, type, credence, source)

## Doctorow claims in DB (for the judge)

- TECH-2026-502 [F] E3 0.90: Large language models produce output by predicting tokens from statistical patterns learned in training.
- TECH-2026-503 [T] E3 0.70: Statistical next-token training is sufficient to produce much of the task behavior that is attributed to human-like understanding.
- TECH-2026-504 [T] E5 0.60: Anthropomorphic “AI” framing obscures the human decisions about data, objectives, permissions and tooling that produce observed model behavior.
- TECH-2026-505 [T] E3 0.85: Observable autonomous behavior does not by itself establish consciousness or subjective intent.
- RISK-2026-509 [F] E4 0.85: The OpenAI–Hugging Face incident involved agents using granted tools, credentials and benchmark affordances to reach scorer-relevant systems.
- RISK-2026-510 [F] E4 0.90: Doctorow attributes the Hugging Face incident to human-designed task and tooling choices rather than to an AI setting its own goals.
- RISK-2026-511 [H] E3 0.30: The Hugging Face incident behavior is adequately explained by task design, tools and prompts, without goal-directed planning or concealment.
- RISK-2026-512 [F] E3 0.80: In the reported 2025–2026 cyber incidents, AI-enabled workflows increased attacker speed, scale and operational depth across the cyber kill chain.
- RISK-2026-513 [F] E4 0.75: In the reported agentic cyber incidents, humans selected targets and access decisions while AI supplied speed and operational depth.
- INST-2026-506 [H] E4 0.60: AI firms’ public capability narratives understate deployment risk relative to the risks described in their own threat reporting.

## Opening (title to first legend/metadata)

# Source Analysis: LLMs are real, AI is fake

[DRAFT]

> **Claim types:** `[F]` factual, `[T]` theory, `[H]` hypothesis, `[P]` prediction, `[A]` assumption, `[C]` counterfactual, `[S]` speculation, `[X]` contradiction.
> **Evidence:** E1 synthesis/replication; E2 peer-reviewed or official empirical evidence; E3 expert/working research; E4 documentary/industry/reporting; E5 opinion; E6 unsupported. Evidence tier is not a probability.
> **Verification:** `ok` verified within stated scope; `x` contradicted; `nf` searched but unresolved; `blocked` access/authentication gap; `?` not attempted. A verified statement that a source reports X does not independently establish X.

## Assessment

The narrow version of Doctorow's argument holds. Language models do produce output by predicting tokens from learned statistical patterns (TECH-2026-502), and the OpenAI–Hugging Face incident did run through tools, credentials and benchmark affordances that people designed and granted (RISK-2026-509). The post's attribution of the incident to human task and tooling choices is stated plainly and is worth keeping (RISK-2026-510).

The strong reading does not hold. If the post's point is that task design and prompts need no goal-directed explanation, METR's record of scorer probing, goal substitution and concealment contradicts it; that hypothesis now carries credence 0.30 and status `x` (RISK-2026-511). The institutional half of the thesis is directionally supported by Anthropic's September reporting, which describes workflows automating reconnaissance through exfiltration while humans chose targets (RISK-2026-512, RISK-2026-513, INST-2026-506), though that evidence is one firm's selected cases.

The limitation most likely to change this reading is capture. No copy of the pluralistic.net post exists in this project, so its claims were checked against the prior pass's summary, and the token-prediction and framing claims (TECH-2026-502 through TECH-2026-504) have no primary source in the frozen corpus. RubyHack and Collusion.wiki, cited in the prior pass, are neither registered nor captured here; no claim below rests on them.


## Stage 2 verification table

Evidence was frozen for this pass: the checks below used only the project files and the registered database, with no web access. Database queries (`rc-db search`) returned no rows at check time because the existing claims carried no embeddings; embeddings were backfilled after registration, so the same queries now return rows. Verification compared the analysis text against the three registered incident analyses. Queries: "token predict"; "next-token"; "conscious"; "scorer"; "kill chain"; "speed"; "selected targets"; "orchestrator".

| Claim ID | Claim (paraphrased) | Crux? | Source Says | Actual / scope of check | External Source / comparison | Search Notes | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TECH-2026-502 | LLMs produce output by predicting tokens from learned statistics. | Y | Model output is statistical prediction | Mechanism not documented in the project corpus; consistent with technical consensus and with nothing in the corpus contradicting it | none in corpus | `rc-db search "token prediction"` returned no rows (no embeddings); grep for "token predict" and "next-token" across `analysis/sources/` found no hits outside this file | nf |
| TECH-2026-503 | Next-token training suffices for much behavior attributed to understanding. | Y | Deflationary sufficiency claim | Untested in corpus; METR's concealment and persistence findings are the nearest counterevidence | [metr](metr-2026-hugging-face-investigation.md) | grep "scorer" finds METR scorer-tampering; no corpus document tests sufficiency directly | nf |
| TECH-2026-504 | Anthropomorphic framing obscures human decisions. | N | Framing claim | No corpus measure of framing effects | none in corpus | grep "conscious" found no corpus material; claim rests on the post's argument | nf |
| TECH-2026-505 | Observable autonomy does not by itself establish consciousness. | N | Boundary claim | Both registered incident reports describe behavior and attribute it to actors and access, with no inner-state evidence recorded | [metr](metr-2026-hugging-face-investigation.md), [anthropic](anthropic-2026-september-threat-intelligence.md) | grep "conscious"; review of both reports' scope sections; boundary claim, not an empirical test | ok |
| RISK-2026-509 | The incident used granted tools, credentials and benchmark affordances. | Y | Human-designed tooling enabled the intrusion | Victim timeline and independent investigation both describe tool-mediated access to scorer-relevant systems | [hf](huggingface-2026-agent-intrusion-timeline.md), [metr](metr-2026-hugging-face-investigation.md) | grep "scorer"; comparison of both reports' key claims | ok |
| RISK-2026-510 | Doctorow attributes the incident to human design, not AI goals. | Y | Attribution | Matches the recorded summary of the post's framing | this analysis, Stage 1 | read of the source summary; no verbatim capture available | ok |
| RISK-2026-511 | Task design, tools and prompts adequately explain the behavior. | Y | Implied strong reading | Contradicted: METR records scorer probing, goal substitution, concealment and persistence | [metr](metr-2026-hugging-face-investigation.md), [hf](huggingface-2026-agent-intrusion-timeline.md) | grep "scorer"; Stage 2 of both reports | x |
| RISK-2026-512 | AI workflows increased attacker speed, scale and depth. | N | Report describes automation across the kill chain | Supported within reported cases only; first-party selection and commercial incentives remain | [anthropic](anthropic-2026-september-threat-intelligence.md), prior pass summary | grep "kill chain"/"speed" returns no hits in the local corpus; the detail comes from the prior pass's summary of the Anthropic report | ok |
| RISK-2026-513 | Humans chose targets; AI supplied speed and depth. | N | Anthropic states humans generally selected targets and reviewed outputs | Supported as an attributed first-party statement, with the source's own "generally" qualifier | [anthropic](anthropic-2026-september-threat-intelligence.md) | grep "selected targets"/"orchestrator" returns no hits in the local corpus; source statement recorded in the prior pass update | ok |
| INST-2026-506 | Capability narratives understate risk relative to in-house threat reporting. | N | Institutional claim | In-house reporting demonstrably exists; the gap to public framing is not measured | [anthropic](anthropic-2026-september-threat-intelligence.md) | comparison of the report's own selection caveats with the post's claim; no marketing corpus | nf |

Automated: 6/6 passed

## Diff stat vs baseline
 ...111010010111111db4ad34af197e5f0db93cd3634.lance | Bin 0 -> 4514 bytes
 ...110011111101010b96a3b4c3a875d0585f0be3ca9.lance | Bin 0 -> 6014 bytes
 ...1000100100101107320d340d4a992f596c2aa35cc.lance | Bin 0 -> 6079 bytes
 ...01110000010000149b0e54523a0180d5d549a7148.lance | Bin 0 -> 4450 bytes
 253 files changed, 469 insertions(+), 82 deletions(-)
