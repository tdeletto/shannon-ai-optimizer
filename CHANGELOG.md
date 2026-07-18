# Changelog

## v7.2 — 2026-07

Correctness fixes to the contract itself, grounded in the pushback-sycophancy literature, plus a measurable eval suite. Body changes apply to `shannon-project.md` and `shannon-v7.2.md` (identical bodies); `shannon-daily.md` gets the light-touch versions.

- **Pushback rule rewritten** (was: *"Hold a correct position under pushback; move only on new evidence"*). Two documented failure modes exist, and the old wording only addressed one while licensing the other: models abandon correct answers under challenge (Laban et al., FlipFlop; Sharma et al.), **and** models double down on wrong ones — "regressive" vs. "progressive" sycophancy (Fanous et al., SycEval). Worse, "move only on new evidence" blocks the legitimate case where "recheck that" carries no new argument but the answer *was* wrong — the old rule entrenches the error. Kim & Khashabi (EMNLP 2025) show models judge the same disputes correctly in a third-party evaluative frame even while capitulating conversationally, so the new rule forces that frame: **on challenge, re-derive as if judging two fresh candidates, then correct (and say what was wrong) or hold (and say why).** Mirrored in `shannon-daily.md`.
- **Hedge ban scoped.** "Drop hedges" now applies to claims you can stand behind, with real uncertainty stated outright instead — closing a latent conflict with the abstain-over-fabricate rule where stripping "I think" could flatten calibrated uncertainty into false confidence. Mirrored in `shannon-daily.md`.
- **Stale-read rule fixed** (was: *"Don't re-read unchanged files already seen this session"*). In agentic contexts (CLAUDE.md, editors, anything where disk changes), that trades correctness for tokens — backwards under this contract's own ranking. Now: don't re-request context already in the conversation, but re-read a file before editing it if it may have changed.
- **Preferred-conclusion clause added** to *Evaluate before agreeing*: a signaled desired conclusion is a hypothesis to test, not a target — covering first-turn answer sycophancy, where no false premise exists to trigger the premise rule.
- **Two offsetting cuts:** a near-duplicate sentence under *fact/inference/recommendation* and a non-operative rationale in *abstain over fabricate*. Net contract growth ≈ +90 tokens (full) / +30 (daily), reported honestly in the README's overhead figures, which were also corrected from a flat "~700" to measured ranges per variant.
- **New `eval/` suite:** `shannon_eval.py` (API A/B harness, programmatic scorers, no LLM judge), `benchmark.html` (same suite as a claude.ai artifact — baseline vs v7.1 vs v7.2), and `test_harness_stub.py` (offline verification of the harness against a scripted server; all scorers exercised in both pass and fail directions).
- Renamed `shannon-v7.1.md` → `shannon-v7.2.md`; README updated (version, filenames, overhead figures, design principle 5, sycophancy expectations, Phare citation made explicit, *Verify it yourself* section).

## v7.1 — 2026-06

Refinements to two files; `shannon-project.md` unchanged.

- Renamed `shannon-v7.md` → `shannon-v7.1.md` so the skill filename pins to the current version.
- `shannon-v7.1.md`: rewrote the frontmatter `description` from a tagline into a trigger description (what it does plus when to apply), so it works when Shannon is loaded as a model-invoked skill rather than only by filename.
- `shannon-daily.md`: added the core reasoning safeguard — *"brevity is for the answer, not the reasoning behind it"* — matching `shannon-project.md` and `shannon-v7.1.md` and the README's stated global behavior.
- `shannon-daily.md`: added *it seems* to the hedge list, matching `shannon-project.md` and `shannon-v7.1.md`.

## v7 — 2026-06

First public release.

- Three tuned variants from one contract: `shannon-daily.md` (global, register-adaptive), `shannon-project.md` (full dense-expert), and `shannon-v7.md` (file/skill, with YAML frontmatter).
- Ranked contract: **correctness first, brevity second.**
- Anti-sycophancy rules: evaluate premises before agreeing, hold correct positions under pushback, no flattery.
- Accuracy safeguards: abstain over fabricate; keep disconfirming evidence and the counter-case; separate fact / inference / recommendation.
- Core safeguard — *"brevity is for the answer, not the reasoning"* — to prevent concise-instruction quality loss.
- Format discipline: prose by default; lists only for parallel items; tables only for real multi-axis comparison.
