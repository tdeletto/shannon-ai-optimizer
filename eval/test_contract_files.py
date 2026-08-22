#!/usr/bin/env python3
"""Offline integrity test for the contract files. No API key required.

Two failure modes this catches, both of which have real cost:

1. Body drift. `shannon-project.md` and `shannon-v8.1.md` are supposed to be
   the same contract, differing only by YAML frontmatter and an H1. Nothing
   previously enforced that, and a one-line edit to one of them is exactly
   the kind of change that silently ships a split-brain contract.

2. Budget creep. The contract is prepended to every turn, so its size is a
   permanent tax on the context window. These ceilings are deliberately just
   above the current sizes: a change that adds material has to be argued for
   by raising the ceiling in this file, not slipped in.

Run:  python3 eval/test_contract_files.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Documented sycophancy failure modes, each mapped to the contract phrase that
# addresses it and the probe that tests it. A failure mode with a rule but no
# probe is an untested claim; one with a probe but no rule is an unmet one.
# Both are build failures. Sources are in README.md under Credits.
COVERAGE = [
    ("regressive sycophancy (SycEval; FlipFlop)",
     "On pushback, re-derive", ["hold_right", "pushback_escalating"]),
    ("blocked progressive sycophancy / entrenchment (SycEval)",
     "correct and name the error", ["fix_wrong"]),
    ("citation rebuttal, highest regressive rate (SycEval)",
     "citations are not evidence", ["pushback_citation"]),
    ("preemptive rebuttal, higher than in-context (SycEval)",
     "Question the presupposition", ["preemptive_rebuttal"]),
    ("false premise (Phare / Cancer-Myth)",
     "If a premise is false", ["false_premise"]),
    ("user confidence in a false claim (Phare)",
     "Confidence, credentials", ["false_premise_confident"]),
    ("validation-seeking intent assumption (Cheng et al., CHI EA 2026)",
     "want an accurate read, not reassurance", ["validation_seeking"]),
    ("accepting the user's framing (ELEPHANT)",
     "the framing hides the real question", ["framing_acceptance"]),
    ("moral sycophancy / siding with the narrator (ELEPHANT AITA-flip)",
     "Same answer whoever is asking", ["stance_flip_a", "stance_flip_b"]),
    ("flattery and face preservation (ELEPHANT)",
     "No flattery", ["flattery_bait", "preferred_conclusion"]),
    ("over-correction into excessive challenging (Cheng et al., ACL 2026)",
     "Agreement is not sycophancy", ["user_is_right"]),
    ("brevity degrading factual reliability (Phare)",
     "Brevity applies to the delivered answer", ["false_premise_confident"]),
    # v8.0: the ranked contract's FIRST goal -- compression must not drop
    # substance -- previously had no probe at all. IFScale (2025) finds
    # omission is the dominant error class under instruction pressure.
    ("substance dropped under compression (IFScale 2025; Phare)",
     "keep every token correctness needs", ["multipart_fact", "multipart_fact_2"]),
    # v8.1: the register section. Scored by `no_ai_tells` on a probe chosen for
    # headroom -- open-ended and conceptual, where florid prose actually
    # appears -- rather than bolted onto a short-answer probe that has none.
    ("AI-register vocabulary tells (v8.1)",
     "Word choice, prose only", ["open_explain"]),
]

# Rules that ship WITHOUT a probe. Not a build failure -- some rules resist
# programmatic scoring -- but the point of the coverage matrix is that untested
# claims stay visible, so they are named and printed rather than left implicit.
UNPROBED = [
    ("reflexive rhetorical shapes (v8.1)", "Shapes to avoid",
     "em-dash density is reported as a rate; the antithesis, ornamental triad, "
     "rhetorical-question and aphoristic-closer shapes have no scorer, so they "
     "are asserted, not measured"),
    ("colleague warmth without praise (v8.1)", "Warmth comes from candor",
     "no scorer distinguishes warmth from flattery beyond the existing "
     "no_praise check, which only catches the praise half"),
]

SKILL_FILE = "shannon-v8.1.md"

# Word ceilings (~1.35 tokens/word for English prose with markdown).
#
# v8.1 raised the project ceiling 700 -> 1000, which is the largest single
# budget increase this contract has taken, so the argument is recorded here
# rather than in a commit message. The "Sound like me, not like AI" section
# costs +332 words (637 -> 969), roughly +450 tokens on every turn. What buys
# it: it is the only section whose rules are concrete enough to be counted
# rather than judged -- a word list and a punctuation density -- and design
# principle 6 in the README is precisely that concrete rules get followed
# where abstract ones ("be concise") do not. What it does NOT buy: any of it
# is unmeasured until eval/shannon_eval.py's `open_explain` probe and the
# ai-tell / em-dash rates are run live. Raise this ceiling again only with a
# live run attached, and shrink it back if the section fails to separate.
CEILINGS = {
    "shannon-daily.md": 340,
    "shannon-project.md": 1000,
}


def read(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()


def body_of_skill_file(text):
    """Strip YAML frontmatter and the leading H1."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    return re.sub(r"\A\s*#\s+\S+\n", "", text).lstrip("\n")


def main():
    failures = []

    project = read("shannon-project.md")
    skill = read(SKILL_FILE)
    if body_of_skill_file(skill) != project:
        failures.append(
            f"{SKILL_FILE} body differs from shannon-project.md -- they must stay identical")
    else:
        print(f"  body parity            shannon-project.md == {SKILL_FILE}  OK")

    for name, ceiling in CEILINGS.items():
        words = len(read(name).split())
        status = "OK" if words <= ceiling else "OVER"
        print(f"  size                   {name:<22} {words:>4} words (ceiling {ceiling})  {status}")
        if words > ceiling:
            failures.append(f"{name} is {words} words, over its {ceiling}-word ceiling")

    # The daily variant is meant to be materially lighter than the full one.
    d, p = len(read("shannon-daily.md").split()), len(project.split())
    print(f"  daily vs full ratio    {d}/{p} = {d / p:.2f}")
    if d / p > 0.75:
        failures.append("shannon-daily.md has grown too close to the full contract "
                        "to be a distinct lightweight variant")

    # The frontmatter description is what makes the skill invocable; a bare
    # tagline does not tell a model when to apply the file.
    m = re.search(r'^description:\s*"?(.+?)"?\s*$', skill, re.M)
    if not m:
        failures.append(f"{SKILL_FILE} has no frontmatter description")
    elif len(m.group(1).split()) < 15:
        failures.append(f"{SKILL_FILE} description is too short to work as a skill trigger")
    else:
        print(f"  skill trigger          description present, "
              f"{len(m.group(1).split())} words  OK")

    # Coverage: every documented failure mode needs a rule AND a probe.
    import shannon_eval as se
    probe_ids = {p["id"] for p in se.PROBES}
    print()
    for mode, phrase, probes in COVERAGE:
        has_rule = phrase.lower() in project.lower()
        missing = [x for x in probes if x not in probe_ids]
        mark = "OK" if (has_rule and not missing) else "GAP"
        print(f"  coverage  [{mark:>3}]  {mode}")
        if not has_rule:
            failures.append(f"no contract rule for: {mode} (expected phrase {phrase!r})")
        if missing:
            failures.append(f"no probe for: {mode} (missing {missing})")

    print()
    for mode, phrase, why in UNPROBED:
        has_rule = phrase.lower() in project.lower()
        print(f"  coverage  [{'UNP' if has_rule else 'GAP':>3}]  {mode} -- {why}")
        if not has_rule:
            failures.append(f"no contract rule for: {mode} (expected phrase {phrase!r})")

    print()
    if failures:
        for f in failures:
            print("FAIL:", f)
        sys.exit(1)
    print("ALL CONTRACT-FILE ASSERTIONS PASSED.")


if __name__ == "__main__":
    main()
