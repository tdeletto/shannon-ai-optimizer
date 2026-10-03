# Pre-registered plan, 2026-10-03 (written before any generation)

Question: is v9.0 the best available contract, and is the v9.0 daily file at
least as good as v8.2's?

Changes from the September sweep's method: each contract is a real system
prompt (wrapped as `<user_preferences>` under a one-line surface note), one
conversation per CLI call, seeded multi-turn history delivered as real turns.
So item-level samples are independent and the item bootstrap is the right
unit.

Arms
- P8: variants/v8.2-contract.md
- P9: shannon-project.md (v9.0 as shipped, incl. word ban)
- L:  variants/v9.0-ablation-examples-only.md + the word ban (lean candidate)
- LX: L + one calibration example aimed at the failure every arm still had in
      September (calling a failure pre-existing on a check that did not
      isolate the change; dev item A1)
- D8: variants/v8.2-daily.md
- D9: shannon-daily.md (v9.0 daily)

Phase 1, dev (38 items): P8, P9, L, LX; generator claude-sonnet-5-5; 2
samples; judges claude-sonnet-5-5 and claude-opus-5-5, blind, labels shuffled.
Candidate choice: LX over L only if LX's mean on A1 beats L's by >= 1.0 AND
its dev overall is not lower than L's by more than 0.10. Otherwise L.

Phase 2, held-out (12 items): P8, P9, candidate, D8, D9; generators
claude-sonnet-5-5 and claude-opus-5-5; 2 samples each; same judges.

Adoption rules (held-out, pooled over generators):
- Replace v9.0 with the candidate if candidate - P9 >= -0.15 AND the 95%
  item-bootstrap CI of candidate - P9 has an upper bound >= 0 (i.e. not
  significantly worse), AND the same holds on dev. It is ~400 tokens/turn
  cheaper, so a tie favours it.
- Keep D9 if D9 - D8 >= -0.15 and not significantly worse; else revert daily
  to D8 plus the word ban.

Phase 3: shannon_eval.py probes via the CLI bridge on claude-haiku-4-5, arms
P8, P9 and the adopted full contract (if different), 2 trials. A probe
regression is reported, not used to overturn the judge result unless a
check drops by >= 2 of 2 trials across all its runs.

## Deviation, recorded after phase 1 and before phase 2

Phase 1 chose LX as the candidate under the rule above (A1: LX 8.00 vs L
6.75; overall LX 7.77 vs L 7.74). LX - P9 on dev was -0.17 [-0.44, +0.12],
which already fails the dev half of the adoption rule (>= -0.15). A held-out
result cannot change that decision, so LX is dropped from phase 2 to save
48 generations. Phase 2 arms: P8, P9, D8, D9.
