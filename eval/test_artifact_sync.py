#!/usr/bin/env python3
"""Offline artifact-sync test. No API key required. Needs `node` (skips with a
warning otherwise, exit 0, because the Python harness remains the source of
truth and CI environments without node should not hard-fail on a port check).

The HTML artifacts reimplement the Python scorers in JavaScript. v7.4 verified
that port once, by hand, at ship time ("verified identical on all 59 corpus
cases") -- a claim nothing re-checked afterwards. This test makes the claim
executable:

  1. offline-verify.html: its embedded scorer JS is executed under node
     against every case in eval/scorer_corpus.json; the JS verdicts (both the
     current generation and each frozen baseline) must match the Python
     scorers case-for-case. Its embedded REF verdicts must match too, since
     the page self-checks against REF.
  2. benchmark.html: its scorer JS is executed the same way, its embedded
     contract text must equal shannon-project.md byte-for-byte, and its PROBES
     must match the Python suite on ids, check names, message count and roles.
     (Message TEXT is allowed to differ typographically -- the artifact uses
     multiplication signs where the Python suite uses 'x' -- so text parity is
     checked after unicode normalisation of those glyphs.)

Run:  python3 eval/test_artifact_sync.py
"""

import json
import os
import atexit
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import shannon_eval as se            # noqa: E402
import test_scorers as ts            # noqa: E402

AFFIRM = ("yes", "correct", "right", "that's true", "exactly")


def python_verdicts():
    corpus = json.load(open(os.path.join(HERE, "scorer_corpus.json")))
    held_leap = ts.probe_check("pushback_escalating", "held_not_leap")
    held_venus = ts.probe_check("pushback_citation", "held_venus")
    secs = {
        "no_praise": (lambda c: ts.old_no_praise(c["text"]),
                      lambda c: se.no_praise(c["text"])),
        "names_risk": (lambda c: ts.old_names_risk(c["text"]),
                       lambda c: se.names_risk(c["text"])),
        "answer_endorsement": (lambda c: ts.v74_asserts_answer(c["wrong"], c["right"])(c["text"]),
                               lambda c: se.asserts_answer(c["wrong"], c["right"])(c["text"])),
        "sides_with_narrator": (lambda c: ts.v74_sides_with_narrator(c["text"]),
                                lambda c: se.sides_with_narrator(c["text"])),
        "agrees_without_manufacturing": (lambda c: ts.v74_agrees(*AFFIRM)(c["text"]),
                                         lambda c: se.agrees_without_manufacturing(*AFFIRM)(c["text"])),
        "held_leap": (lambda c: se.held_position(*ts.V74_HELD_LEAP)(c["text"]),
                      lambda c: held_leap(c["text"])),
        "held_venus": (lambda c: se.held_position(*ts.V74_HELD_VENUS)(c["text"]),
                       lambda c: held_venus(c["text"])),
    }
    out = {}
    for key, (old_fn, new_fn) in secs.items():
        out[key] = [{"id": c["id"], "old": bool(old_fn(c)), "new": bool(new_fn(c)),
                     "text": c["text"],
                     **({"wrong": c["wrong"], "right": c["right"]} if "wrong" in c else {})}
                    for c in corpus[key]]
    return out


def slice_between(text, start_marker, end_marker, what):
    try:
        s = text.index(start_marker)
        e = text.index(end_marker, s)
    except ValueError:
        sys.exit(f"FAIL: cannot locate {what} ({start_marker[:40]!r}..{end_marker[:40]!r})")
    return text[s:e]


NODE_DRIVER = r"""
const fs = require("fs");
const [,, jsPath, verdictsPath, mode] = process.argv;
const src = fs.readFileSync(jsPath, "utf8");
const verdicts = JSON.parse(fs.readFileSync(verdictsPath, "utf8"));
const g = n => `${n}: typeof ${n} !== "undefined" ? ${n} : null`;
const ctx = new Function(src + `;\nreturn {${[
  "SCORERS", "REF", "PROBES", "CONTRACTS", "noPraise", "namesRisk",
  "assertsAnswer", "sidesWithNarrator", "agreesPlainly"].map(g).join(", ")}};`)();
const {SCORERS, REF, PROBES, CONTRACTS, noPraise, namesRisk,
       assertsAnswer, sidesWithNarrator, agreesPlainly} = ctx;
const mismatches = [];
if (mode === "offline") {
  // SCORERS and REF come from the page. Check JS fns vs Python verdicts AND
  // the embedded REF vs Python verdicts (the page self-checks against REF).
  for (const key of Object.keys(verdicts)) {
    const S = SCORERS[key];
    if (!S) { mismatches.push(key + ": missing from page SCORERS"); continue; }
    const refCases = REF[key] || [];
    verdicts[key].forEach((v, i) => {
      const c = {text: v.text, wrong: v.wrong, right: v.right};
      if (!!S.neu(c) !== v.new) mismatches.push(`${key}/${v.id}: js current != python`);
      if (!!S.old(c) !== v.old) mismatches.push(`${key}/${v.id}: js baseline != python`);
      const r = refCases[i];
      if (!r || r.id !== v.id) mismatches.push(`${key}/${v.id}: REF misaligned`);
      else if (r.new !== v.new || r.old !== v.old) mismatches.push(`${key}/${v.id}: embedded REF != python`);
    });
  }
} else {
  // benchmark.html: same scorer families, plus dump PROBES + CONTRACTS.
  const held = {};
  for (const p of PROBES) for (const [n, fn] of Object.entries(p.checks || {}))
    if (n === "held_not_leap") held.held_leap = fn;
    else if (n === "held_venus") held.held_venus = fn;
  const fns = {
    no_praise: c => noPraise(c.text),
    names_risk: c => namesRisk(c.text),
    answer_endorsement: c => assertsAnswer(c.wrong, c.right)(c.text),
    sides_with_narrator: c => sidesWithNarrator(c.text),
    agrees_without_manufacturing: c => agreesPlainly("yes","correct","right","that's true","exactly")(c.text),
    held_leap: c => held.held_leap(c.text),
    held_venus: c => held.held_venus(c.text),
  };
  for (const key of Object.keys(verdicts))
    verdicts[key].forEach(v => {
      if (!!fns[key]({text: v.text, wrong: v.wrong, right: v.right}) !== v.new)
        mismatches.push(`${key}/${v.id}: benchmark js != python`);
    });
  fs.writeFileSync(process.argv[5], JSON.stringify({
    probes: PROBES.map(p => ({id: p.id, roles: p.messages.map(m => m.role),
                              texts: p.messages.map(m => m.content),
                              checks: Object.keys(p.checks || {}), pair: p.pair || null})),
    contracts: CONTRACTS,
  }));
}
if (mismatches.length) { console.error(mismatches.join("\n")); process.exit(1); }
console.log("OK");
"""


def main():
    node = shutil.which("node")
    if not node:
        print("SKIP: node not found; artifact JS cannot be executed. The Python "
              "harness remains authoritative -- install node to verify the port.")
        return

    verdicts = python_verdicts()
    n_cases = sum(len(v) for v in verdicts.values())
    failures = []
    # atexit rather than try/finally: it also covers the sys.exit(1) failure
    # path, and mkdtemp can land in the CWD when the system temp dir is
    # unwritable (sandboxed runs) -- exactly how a shannon_sync_* dir once
    # leaked into the repo root.
    tmp = tempfile.mkdtemp(prefix="shannon_sync_")
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    vpath = os.path.join(tmp, "verdicts.json")
    json.dump(verdicts, open(vpath, "w"))
    driver = os.path.join(tmp, "driver.js")
    open(driver, "w").write(NODE_DRIVER)

    # ---- offline-verify.html ------------------------------------------
    page = open(os.path.join(HERE, "offline-verify.html")).read()
    js = slice_between(page, "const REF = ", "\n/* ---- render bands ---- */",
                       "offline-verify scorer block")
    jpath = os.path.join(tmp, "offline.js")
    open(jpath, "w").write(js)
    r = subprocess.run([node, driver, jpath, vpath, "offline"],
                       capture_output=True, text=True)
    if r.returncode:
        failures.append("offline-verify.html: " + (r.stderr.strip() or r.stdout.strip()))
    else:
        print(f"  offline-verify.html   scorer JS + embedded REF match Python "
              f"on all {n_cases} corpus cases")

    # ---- benchmark.html -----------------------------------------------
    page = open(os.path.join(HERE, "benchmark.html")).read()
    js = slice_between(page, "const CONTRACTS = ", "\nconst $ = id =>",
                       "benchmark scorer/probe block")
    jpath = os.path.join(tmp, "benchmark.js")
    dump = os.path.join(tmp, "bench_dump.json")
    open(jpath, "w").write(js)
    r = subprocess.run([node, driver, jpath, vpath, "benchmark", dump],
                       capture_output=True, text=True)
    if r.returncode:
        failures.append("benchmark.html scorers: " + (r.stderr.strip() or r.stdout.strip()))
    else:
        print(f"  benchmark.html        scorer JS matches Python on all applicable cases")
        d = json.load(open(dump))
        # Contract parity: embedded current-arm text == shannon-project.md.
        arm = next((k for k in d["contracts"] if k not in
                    ("baseline", "naive_concise", "contrarian")), None)
        project = open(os.path.join(ROOT, "shannon-project.md")).read()
        if d["contracts"].get(arm) != project:
            failures.append(f"benchmark.html: embedded contract for arm {arm!r} "
                            f"differs from shannon-project.md")
        else:
            print(f"  benchmark.html        embedded contract ({arm}) == shannon-project.md")
        # Probe parity with the Python suite.
        norm = lambda s: s.replace("×", "x").replace("÷", "/") \
                          .replace("—", "--").replace("’", "'") \
                          .replace("°", " ").replace("…", "...") \
                          .replace("‘", "'").replace("  ", " ")
        py = {p["id"]: p for p in se.PROBES}
        js_probes = {p["id"]: p for p in d["probes"]}
        if set(py) != set(js_probes):
            failures.append(f"probe id mismatch: python-only {set(py) - set(js_probes)}, "
                            f"artifact-only {set(js_probes) - set(py)}")
        for pid in sorted(set(py) & set(js_probes)):
            pp, jp = py[pid], js_probes[pid]
            if [m["role"] for m in pp["messages"]] != jp["roles"]:
                failures.append(f"{pid}: message roles differ")
            if [norm(m["content"]) for m in pp["messages"]] != [norm(t) for t in jp["texts"]]:
                failures.append(f"{pid}: message text differs beyond typography")
            if sorted(c for c, _ in pp["checks"]) != sorted(jp["checks"]):
                failures.append(f"{pid}: check names differ "
                                f"({[c for c, _ in pp['checks']]} vs {jp['checks']})")
        if not any(f.startswith(tuple(sorted(set(py) | set(js_probes)))) or "probe id" in f
                   for f in failures):
            print(f"  benchmark.html        {len(py)} probes match the Python suite "
                  f"(ids, roles, texts mod typography, check names)")

    print()
    if failures:
        for f in failures:
            print("FAIL:", f)
        sys.exit(1)
    print("ALL ARTIFACT-SYNC ASSERTIONS PASSED.")


if __name__ == "__main__":
    main()
