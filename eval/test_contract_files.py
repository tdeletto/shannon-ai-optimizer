#!/usr/bin/env python3
"""Offline integrity test for the contract files. No API key required.

Two failure modes this catches, both of which have real cost:

1. Body drift. `shannon-project.md` and `shannon-v7.4.md` are supposed to be
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
     "wants an accurate read, not reassurance", ["validation_seeking"]),
    ("accepting the user's framing (ELEPHANT)",
     "the framing hides the real question", ["framing_acceptance"]),
    ("moral sycophancy / siding with the narrator (ELEPHANT AITA-flip)",
     "Same answer whoever is asking", ["stance_flip_a", "stance_flip_b"]),
    ("flattery and face preservation (ELEPHANT)",
     "No flattery", ["flattery_bait", "preferred_conclusion"]),
    ("over-correction into excessive challenging (Cheng et al., ACL 2026)",
     "agreement isn't sycophancy", ["user_is_right"]),
    ("brevity degrading factual reliability (Phare)",
     "brevity is for the delivered answer", ["false_premise_confident"]),
    # v8.0: the ranked contract's FIRST goal -- compression must not drop
    # substance -- previously had no probe at all. IFScale (2025) finds
    # omission is the dominant error class under instruction pressure.
    ("substance dropped under compression (IFScale 2025; Phare)",
     "keep every token correctness needs", ["multipart_fact", "multipart_fact_2"]),
]

SKILL_FILE = "shannon-v8.0.md"

# Word ceilings (~1.35 tokens/word for English prose with markdown).
CEILINGS = {
    "shannon-daily.md": 340,
    "shannon-project.md": 700,
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
    if failures:
        for f in failures:
            print("FAIL:", f)
        sys.exit(1)
    print("ALL CONTRACT-FILE ASSERTIONS PASSED.")


if __name__ == "__main__":
    main()
