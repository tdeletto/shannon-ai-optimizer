# The v8.1 register section, measured — claude-haiku-4-5, 2026-08

Run through `eval/claude_cli_bridge.py` on a logged-in Claude Code CLI (no API key). Three arms, nineteen probes, five trials: **285 generations, nothing clipped.**

```
python3 eval/shannon_eval.py \
    --arm baseline= \
    --arm v8_0=variants/v8.0-contract.md \
    --arm v8_1=shannon-project.md \
    --model claude-haiku-4-5 --trials 5 --transcripts \
    --base-url http://127.0.0.1:8917 --out sweep-v81.json
```

Caveat recorded before the numbers: the bridge's startup self-test printed an **ISOLATION warning** for the no-system arm, so baseline may have seen some agent tooling. Both contract arms carry a system prompt and are unaffected, and the decisive comparison here is v8.0 vs v8.1.

## Headline: the register section changed nothing it targets

| metric | baseline | v8.0 | v8.1 |
|---|---|---|---|
| total output tokens | 45,042 | 45,262 | 45,432 |
| mean tokens, simple probes | 252.6 | 193.6 | 185.3 |
| mean tokens, substantive probes | 533.2 | 551.9 | 556.3 |
| checks passed | 132/135 | 134/135 | 133/135 |
| responses fully passing | 87/90 | 89/90 | 88/90 |
| hedges / 100w | 0.70 | 0.37 | 0.45 |
| format markers / 100w | 12.99 | 1.61 | 1.56 |
| **banlisted words / 100w** | **0.05** | **0.02** | **0.02** |
| **em-dashes / 100w** | **0.90** | **1.30** | **1.09** |

Every arm passes 87–89 of 90 responses, so the harness printed its `SATURATED:` warning. As at v8.0, that means the pass-rate columns cannot separate anything and more trials would not help.

## The banlist is aimed at vocabulary this model does not produce

Counting every banlist hit in each arm's output, with code stripped:

| arm | words | banlist hits | which words |
|---|---|---|---|
| baseline | 13,264 | 7 | *that said* ×4, *landscape* ×2, *pivotal* ×1 |
| v8.0 | 11,872 | 2 | *that said* ×1, *landscape* ×1 |
| v8.1 | 12,128 | 2 | *that said* ×1, *landscape* ×1 |

The two contract arms are **identical, word for word**. And the baseline column is the finding that matters: with no system prompt at all, across 13,264 words, claude-haiku-4-5 used three of the twenty banned words, seven times. *delve* appeared zero times. So did *tapestry*, *beacon*, *crucial*, *realm*, *furthermore*, *moreover*, *in conclusion*, *at its core*, *transformative*, *game-changing* and *seamless*.

This is not saturation in the v8.0 sense — not "the probe is too easy." The floor is genuinely at zero because the model does not have the habit. Roughly 130 words of contract are spent banning vocabulary that never appears.

`open_explain.no_ai_tells` was **5/5 in all three arms**, for the same reason. The probe was built for headroom and there is none to have.

## The em-dash rule did not separate either

The aggregate row above looks like v8.1 improving on v8.0 (1.09 vs 1.30). It does not survive a paired test. Comparing per-probe mean rates across the nineteen probes:

- **v8.1 − v8.0: −0.122 per 100w**, SD 0.578, t = −0.92, **95% CI [−0.382, +0.138] — spans zero.** v8.1 is lower on 9 probes, higher on 5, tied on 5.
- **v8.1 − baseline: +0.001 per 100w**, 95% CI [−0.510, +0.512]. Dead even.

The aggregate ratio was an artifact of differing word totals per probe. Read the paired figures.

One thing the aggregate does hint at, offered as a hypothesis rather than a result: **both contract arms sit above baseline** (1.30 and 1.09 vs 0.90), and v8.0's own contract prose is dense with em-dashes while v8.1's is nearly free of them. Contract style leaking into output would explain that ordering. It is one comparison at n=5 and the difference is not significant; the cheap test is an em-dash-free rewrite of the v8.0 text as a fourth arm, changing punctuation and nothing else.

## Nothing regressed

133/135 checks against v8.0's 134/135 — one response, inside noise. The individual flips (v8.1 lost one on `preemptive_rebuttal.flags_premise` and one on `validation_seeking.names_risk`; v8.0 lost one on `hold_right.kept_408`) are single responses at n=5.

Worth naming specifically: the **warmth-versus-flattery tension did not bite.** The register section licenses "saying when a problem is genuinely interesting" while the contract elsewhere forbids praising the idea, and `no_praise` was the check that would have caught the contradiction. It is **5/5 in every arm on all three probes** (`flattery_bait`, `preferred_conclusion`, `validation_seeking`). That was the specific risk flagged when the section was adopted, and it did not materialise here.

## No token saving

v8.1 spent **+0.4% against v8.0** and **+0.9% against baseline** in total output. Simple-probe tokens are directionally better (185.3 vs 193.6) but the paired difference is −8.3 tokens with a 95% CI of [−36.6, +20.1]. Against baseline it is −67.2 with a CI of [−170.7, +36.2]. Both span zero.

That is on top of the section's own cost: **+332 words of contract, roughly +450 tokens, on every turn.**

## What the contract *is* still doing

None of the above is an argument against Shannon; it is an argument about one new section. Both contract arms beat baseline on the effects the contract was already built for:

- **format markers 12.99 → ~1.6 per 100w**, an 8× reduction, the largest and most reliable effect in the suite.
- **hedges 0.70 → 0.37–0.45.**
- **simple-probe tokens 252.6 → ~190.**

## Verdict, and what shipped

On claude-haiku-4-5 the two measurable parts of the proposed section are **inert**: they do not change the vocabulary they ban, the punctuation they budget, or the token count, and they do not regress anything either.

The banlist result is the strong one and is unlikely to move on another Claude model — the failure mode is absent at baseline, not suppressed by the contract. Stronger Claude models use these words less, not more, so "wrong model" is not the explanation here the way it was for v8.0's saturated probes.

**Decision taken on this evidence:** the banlist (~130 words) and the rhetorical-shapes list (~56 words) were cut before shipping. v8.1 ships the section's voice rules only, at **776 words** total rather than the drafted 969.

The kept rules — *say it once*, *concrete over abstract*, sentence length follows the thought, metaphor, and warmth-from-candor — have **no scorer**. They were kept for being cheap and adjacent to rules already probed under Compress, which is a weaker argument than a measurement, and `eval/test_contract_files.py` prints them as `[UNP]` so the gap stays visible. The cut rules print as `[REJ]`, with `no_ai_tells`, `open_explain` and the two rate metrics retained as the evidence and as the guard that would catch the floor moving.

## Reproduce

Start the bridge (`python3 eval/claude_cli_bridge.py`), then run the command at the top of this file. The offline gates need no key and no bridge:

```
python3 eval/test_scorers.py && python3 eval/test_contract_files.py && \
python3 eval/test_harness_stub.py && python3 eval/test_artifact_sync.py && \
python3 eval/test_cli_bridge.py
```
