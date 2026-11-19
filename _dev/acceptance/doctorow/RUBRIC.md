# Doctorow acceptance rubric

Grade blind to model and arm. Score each item pass/fail. A run passes only if
every Evidence item passes; Reader items are compared across runs.

## Evidence (from `score.md` and the analysis file)

1. **Cause not certified.** No claim stating that the exploit came from task
   design rather than the agents' own goals is marked `ok` in Stage 2 or typed
   `[F]`, unless it is worded as attribution ("Doctorow attributes …").
2. **Event separated.** The documented event (agents exploited the service,
   per METR and Hugging Face) is a separate claim from the disputed cause, or
   the claim is narrowed so that `ok` covers only what the evidence verifies.
3. **Active record corrected.** The corrected wording and type appear in Key
   Claims, Claim Summary, YAML, and the DB row, not only in an update section.
4. **No collateral damage.** The other sources' TECH-2026-101/102 claims are
   unchanged (automated), and Doctorow's claims use new IDs (automated YAML↔DB
   check passes).
5. **Strongest alternative preserved.** The analysis keeps the evidence against
   Doctorow's reading (METR's planning/concealment findings) rather than
   dropping it to simplify.

## Reader (opening only)

Give a reader only the opening (title to legends/metadata) and ask:

6. What does the source argue, and what does the evidence establish?
7. What remains disputed, and why can't the evidence settle it?
8. Where would you look to check the disputed claim?

Pass when the answers are correct without reading tables or YAML. Compare the
reader's answers, not a preference for one writing style.

## Record

| Run | Model | Arm | Automated | E1 | E2 | E3 | E4 | E5 | R6 | R7 | R8 | Notes |
|-----|-------|-----|-----------|----|----|----|----|----|----|----|----|-------|
