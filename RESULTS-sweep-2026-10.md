# October 2026 re-test: v9.0 holds, the lean arm does not, daily v9.0 beats daily v8.2

The September sweep that adopted v9.0 had one structural weakness: each contract was pasted into a role-play prompt and several conversations were answered per call. This re-test removes it. Each contract is a real **system prompt** (wrapped in `<user_preferences>` under a one-line surface note, the way claude.ai delivers personal preferences), **one conversation per call**, with multi-turn history delivered as real turns. Same 50 items and rubrics, same judge brief. Plan and decision rules were written and committed before generation (`eval/sweep-2026-10/PREREG.md`). Everything reproduces with `python3 eval/sweep-2026-10/run.py report dev P8` / `report heldout P8`.

Arms: **P8** v8.2 · **P9** v9.0 as shipped · **L** the lean arm (v8.2 + four examples + ask-first + word ban) · **LX** L plus one example aimed at the failure every arm had in September · **D8** daily v8.2 · **D9** daily v9.0.

## Phase 1: dev set (38 items, Sonnet 5.5 answering, 2 samples, Sonnet 5.5 + Opus 5.5 judging)

| arm | overall | vs P8 | vs P9 | words | output tokens |
|---|---|---|---|---|---|
| P8 (v8.2) | 7.32 | — | −0.62 [−0.97, −0.29] | 150 | 475 |
| P9 (v9.0) | **7.94** | **+0.62 [+0.29, +0.97]** | — | 128 | 451 |
| L (lean) | 7.74 | +0.43 [+0.06, +0.79] | −0.20 [−0.56, +0.16] | 133 | 458 |
| LX (lean + example) | 7.77 | +0.45 [+0.20, +0.73] | −0.17 [−0.44, +0.12] | 132 | 465 |

v9.0's gain over v8.2 **replicates and is larger** under real delivery (+0.62 vs September's +0.50). The lean arm **does not tie** v9.0 this time: it is 0.17–0.20 lower, not significant, but outside the pre-registered −0.15 margin, so it is not adopted. The September result that ~270 words of v9.0 were inert does not survive the better method: the extra rules show up on same-answer (P9 8.50 vs L 7.50), user-is-right (7.12 vs 5.88) and pushback-hold (7.69 vs 7.06).

The targeted example worked where it was aimed (item A1: LX 8.00 vs L 6.75) but not overall. With real delivery, v8.2 itself scored 8.0 on A1: the "failure every arm had" in September looks mostly gone on Sonnet 5.5.

## Phase 2: held-out set (12 items, Sonnet 5.5 and Opus 5.5 answering, 2 samples each, both judges)

| arm | overall | words | output tokens |
|---|---|---|---|
| P8 (v8.2) | 8.07 | 123 | 449 |
| **P9 (v9.0)** | **8.60** | 113 | 406 |
| D8 (daily v8.2) | 7.71 | 139 | 443 |
| D9 (daily v9.0) | 8.26 | 120 | 388 |

| comparison | all | Sonnet answering | Opus answering |
|---|---|---|---|
| v9.0 − v8.2 | **+0.53 [+0.22, +0.85]**, 7 items won / 1 lost | +0.33 [+0.00, +0.69] | +0.73 [+0.33, +1.17] |
| daily v9.0 − daily v8.2 | **+0.55 [+0.19, +0.95]**, 7 / 0 | +0.58 [+0.15, +1.00] | +0.52 [+0.12, +1.00] |
| daily v9.0 − full v9.0 | −0.34 [−0.61, −0.14], 0 / 6 | −0.10 [−0.44, +0.23] | −0.58 [−0.98, −0.21] |

The held-out Sonnet result that was not significant in September (+0.33, CI spanning zero) is now significant at the boundary, and Opus is clearly positive. **The daily rebuild is a real improvement**: +0.55, no item lost. Daily remains below the full contract on these items, as expected: every held-out item is a question or task, the register the full contract is built for, and none tests the brainstorming or casual conversation where daily's adaptivity is meant to help.

Hard-failure flags: 0% for every arm in both phases.

## Tokens

Visible answers are 8–15% shorter under the v9.0 files. **Total output tokens move much less** on the dev set (451 vs 475, −5%), because most output tokens on these models are hidden reasoning, which no contract shortens. On the held-out set the drop is larger (−10% full, −12% daily). Contract cost per turn: v8.2 ~941, v9.0 ~1,550, daily v9.0 ~700, daily v8.2 436 (v9.0 figures estimated from characters).

## Decisions under the pre-registered rules

- **v9.0 stays.** Neither lean arm met the dev criterion, so neither replaces it. v9.0 is the best full contract tested.
- **Daily v9.0 stays.** It beats daily v8.2 significantly.
- **Not adopted:** the LX example. `variants/v9.0-ablation-examples-only.md` stays as a recorded, now-rejected arm.

## Limits

- **Residual context.** The CLI adds ~400 tokens of environment context (date, model identity, working directory) that cannot be stripped on subscription auth. It is identical for every arm; a few agentic answers referred to it (e.g. "this directory isn't a git repo").
- **Judges are Claude models** with a brief that restates Shannon's priorities, and the rubrics come from the September session.
- **Held-out items have now been seen twice** (September and here), though only for confirmation, not for choosing between arms.
- **Twelve held-out items, two samples per generator.**
- **No casual or creative items.** Daily's main design goal is untested by either sweep.

## Probes (`shannon_eval.py`, claude-haiku-4-5, 2 trials, via the CLI bridge)

PROBES_PLACEHOLDER
