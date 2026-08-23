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

## Follow-up: the burstiness hypothesis, tested — and it was backwards

The three-arm sweep suggested both contracts *flatten* cadence: baseline 14.38, v8.2 9.03, rewrite 9.99. That was published as a hypothesis. **It was an artifact of the metric, and the sign reverses once the artifact is removed.**

Five arms, four prose probes, eight trials: 160 generations, separating hypotheses the first run conflated.

| arm | n | raw burstiness | format /100w | mean tok |
|---|---|---|---|---|
| baseline | 32 | 12.28 | 9.29 | 573 |
| neutral (`You are a helpful assistant.`) | 32 | 13.04 | 9.78 | 566 |
| naive_concise (`Answer the question briefly.`) | 32 | 11.91 | 8.20 | 474 |
| v8.2 | 32 | 9.18 | 2.20 | 668 |
| v8.2 + explicit "vary sentence length" | 32 | 8.81 | 1.14 | 658 |

On the raw metric, v8.2 is significantly *below* baseline (−3.09, 95% CI [−4.78, −1.41]), while a neutral system prompt (+0.76) and a bare brevity instruction (−0.36) both span zero. So it is not "having a system prompt" and not "being told to be brief."

### The metric was measuring formatting

Pooled across all 160 responses, **format-marker density and raw burstiness correlate at r = +0.546**. The arms separate roughly 4× on formatting (9.29 vs 2.20 per 100 words) and **do not overlap at all**: of 96 responses from the three unstructured arms, *zero* were markdown-free, so the confound cannot be controlled by subsetting.

The mechanism is mechanical. A markdown header is a four-word pseudo-sentence and a bullet is a fragment, so a heavily formatted answer registers as gloriously varied while flowing prose registers as uniform. The raw metric was ranking a bulleted answer above disciplined prose *because* it was bulleted.

### Stripping structure reverses the result

Recomputing over running prose only — headers and list items removed:

| arm | raw | prose-only | share of words that are prose |
|---|---|---|---|
| baseline | 12.28 | **5.69** | 31% |
| neutral | 13.04 | 5.80 | 29% |
| naive_concise | 11.91 | 6.05 | 40% |
| **v8.2** | 9.18 | **8.73** | **82%** |
| v8.2 + clause | 8.81 | 9.09 | 89% |

| vs baseline (prose only) | diff | 95% CI | |
|---|---|---|---|
| neutral | +0.11 | [−1.14, +1.36] | spans zero |
| naive_concise | +0.36 | [−0.69, +1.41] | spans zero |
| **v8.2** | **+3.04** | **[+2.03, +4.05]** | **SIGNIFICANT** (t = +5.90) |
| v8.2 + clause | +3.40 | [+2.28, +4.52] | SIGNIFICANT |

**Shannon produces significantly more varied prose cadence than no contract at all** — the opposite of what the raw metric said. Baseline's apparent variety was 69% of its output being structure rather than prose.

### The explicit instruction does nothing

v8.2 → v8.2 + "vary sentence length deliberately; uniform cadence is the clearest tell of machine prose": **+0.36 prose-only, 95% CI [−0.73, +1.45]**, spanning zero. Raw: −0.37, also spanning zero. Twenty words, no measurable effect, in either direction. This holds the review's burstiness recommendation to the same standard as its banlist, and it fails the same way.

### What was corrected

`burstiness()` now strips markdown structure before measuring, and is reported as **prose cadence SD**. A confounded metric that produces a backwards answer is worse than no metric. The earlier published claim — that both contracts flatten cadence — is **withdrawn**.

An honest limit on the reversal: baseline retains only 31% of its words as prose, so its prose-only figure is computed over a thin, possibly unrepresentative slice (intros and outros). The robust claim is the composition difference — baseline writes 69% structure, Shannon writes 18% — and that within actual prose, Shannon's is more varied. Both cut the same way.
