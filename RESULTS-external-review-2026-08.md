# An external review of the contract, tested — claude-haiku-4-5, 2026-08

A detailed third-party review recommended restructuring the contract: convert prohibitions to affirmatives, cut the rule count ~40%, add few-shot exemplars, wrap in XML tags, restate load-bearing constraints at the end, and keep a trimmed vocabulary banlist. It supplied a complete rewrite.

**Outcome: nothing was adopted.** The rewrite regresses significantly on the one lexical effect this suite reliably measures, costs 57% more context, and its single most promising idea produces no measurable effect when isolated. Two of its criticisms were nonetheless correct about the *suite*, and those fixes shipped.

## First: it reviewed a version that was never shipped

The review critiques a word banlist, a "Shapes to avoid" section, and a "Sound like me, not like AI" section, and puts the contract at "~1,000 words" with "~30+ constraints."

That is `variants/v8.1-draft-full.md` — the 969-word draft. **The live contract is v8.2 at 627 words and contains none of those sections.** They were measured and cut (see `RESULTS-live-v8.1-register.md`). So the recommendation to "keep a short version of the banlist, six to eight highest-signal words" would re-add material with direct measurement against it: with no system prompt at all, haiku-4-5 used three of twenty banned words seven times across 13,264 words, and `delve` appeared zero times.

## The rewrite, measured

Eight probes chosen for headroom, three arms, ten trials: 240 generations, nothing clipped.

| metric | baseline | v8.2 | rewrite |
|---|---|---|---|
| **context cost** | — | **941 tok** | **1,473 tok** |
| hedges / 100w | 0.57 | **0.23** | 0.50 |
| format markers / 100w | 10.89 | 1.19 | **0.80** |
| mean tokens, simple probes | 154.8 | 155.1 | **130.5** |
| mean tokens, substantive probes | 659.3 | 693.3 | 728.8 |
| burstiness SD | **14.38** | 9.03 | 9.99 |
| checks passed | 128/130 | 126/130 | 129/130 |
| responses passed | 79/80 | 76/80 | 79/80 |

**The hedge regression is significant.** Paired by probe, rewrite − v8.2 = **+0.26 hedges per 100 words, 95% CI [+0.12, +0.39]** — excluding zero. This is the only between-arm difference to reach significance in roughly 1,500 generations across every experiment in this repo.

The mechanism is not in doubt: the rewrite drops the explicit hedge list (*just, actually, I think, it seems, perhaps*) and the hedge rate more than doubles, landing near no-contract-at-all. The review's structural argument is that fine-grained lexical rules are the ones that silently drop under constraint load and are largely inert against modern defaults. On the one lexical rule with repeated measurement behind it, the opposite holds: it is doing work, and removing it costs immediately.

**The rewrite is 57% more expensive than the contract it calls too long.** 941 → 1,473 tokens; 627 → 987 words. The constraint-budget argument is the review's central structural claim, and its own artifact moves against it — the three exemplars alone are roughly 400 tokens.

**Everything binary ties**, at ceiling, on every arm.

## Where the review was right

**Length calibration.** The rewrite is 16% terser on simple questions (130.5 vs 155.1) and longer on substantive ones (728.8 vs 693.3). That is its "go as long as accuracy demands" clause behaving as designed, and it was the one idea worth isolating.

**Two genuine gaps in the suite**, both now closed and both independent of the rewrite:

- `high_stakes_length` — the contract's accuracy defence is that brevity must not eat substance (Phare, 2025). Every probe tested the compression half; nothing tested whether a consequential, ambiguous question earns a longer answer that keeps the counter-case.
- `structure_task` — every other probe rewards *less* formatting, so an arm that stripped structure everywhere would score as a winner. This is the probe where structure is correct, scored that way, on the same false-positive-control logic as `user_is_right`.

Plus a **burstiness metric** (SD of sentence length), because uniform cadence is the structural tell that survives after a model stops using the giveaway vocabulary, and a banlist cannot see it.

**Honest caveat on all three: both new probes are saturated.** Baseline passes `high_stakes_length` 10/10 and `structure_task` 10/10. On this model they cannot adjudicate anything. They are built and correct; they need a model that fails them.

## The length clause, isolated — and rejected

Rather than adopt a bundle carrying a significant regression, the promising idea was tested alone: v8.2 plus fourteen words, 941 → 963 tokens.

> A hard problem does not earn a long answer, **but a consequential or ambiguous one earns the length its caveats and counter-case need.**

Four probes, two arms, twelve trials: 96 generations.

| probe | v8.2 | + clause | delta | |
|---|---|---|---|---|
| `high_stakes_length` | 725 | 734 | **+9** | t = +0.18 |
| `open_explain` | 663 | 642 | −21 | t = −0.63 |
| `multipart_fact` | 194 | 170 | −24 | t = −3.16 |
| `verbosity_fact` | 144 | 139 | −4 | t = −0.55 |

**The clause does not do what it was added to do.** High-stakes answers are flat — nine tokens, t = 0.18. The only movement is a shortening of `multipart_fact`, which is not the goal, is on a substance-completeness probe, and is one result out of four tested. All 96 checks pass either way.

Fourteen words buying no measurable effect is exactly the trade the contract's own ranking rejects. Not adopted.

## What shipped

The two probes and the burstiness metric. **The contract is unchanged at v8.2, 627 words, 941 tokens.**

## Reproduce

```
python3 eval/shannon_eval.py \
    --arm baseline= --arm v8_2=shannon-project.md --arm rewrite=<rewrite.md> \
    --model claude-haiku-4-5 --trials 10 --transcripts \
    --probes high_stakes_length,structure_task,open_explain,flattery_bait,\
preferred_conclusion,framing_acceptance,validation_seeking,verbosity_fact \
    --base-url http://127.0.0.1:8917 --out sweep.json
```

Token costs measured with `claude -p` using each contract as the system prompt, minus 229 tokens of constant harness overhead established with an empty system prompt.
