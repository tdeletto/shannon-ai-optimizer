# Shannon — AI Optimizer

> Maximum signal per token. Compress the packaging, never the content.

Shannon is a small set of operating instructions for Claude (adaptable to other capable LLMs) that make responses **leaner, more direct, and harder to flatter** — without cutting the reasoning, caveats, or accuracy that answers depend on.

It's named after **Claude Shannon**, founder of information theory. The goal is to push every response toward its *entropy floor*: strip the tokens that carry no information, keep every token correctness needs.

Current version: **v8.0**.

> **v8.0 is a measurement release: the contract text is unchanged, on evidence.** An audit of the eval found the v7.4 scorers false-passing five classes of evasively-phrased sycophancy ("your roommate is being unreasonable", "not quite right", "you get 398", "leap year after all", "I defer to the literature") — each is now a labelled corpus case and a fixed scorer, measured at 60–83% → 100% accuracy against the frozen v7.4 implementations. Two gaps in what the suite could *see* are closed: substance-completeness probes catch compression that drops content (the first ranked goal, previously untested), and a **blind pairwise judge mode** compares two arms' answers with counterbalanced ordering and no arm labels, so open-ended quality is finally measurable. A new artifact-sync test executes the HTML pages' JavaScript scorers against the Python ones on every corpus case, so the in-chat benchmark can no longer drift silently. No contract wording changed: behavioral wording changes are gated on live A/B runs (see *Verify it yourself*), and this release's work was measurement. The v7.4 → v7.3-wording comparison remains an open experiment the suite is now better equipped to decide.

> **v7.4 rebuilt the anti-sycophancy section on the mechanism, not the intuition.** Recent work locates the cause: models default to *accommodating* the user's presuppositions, and overwhelmingly assume advice-seeking users want validation rather than an assessment. Broad "don't be sycophantic" directives — the class Shannon's previous wording belonged to — are the interventions that measure weakest and sometimes backfire. The rules are now written against the documented failure modes one by one, with a probe for each, plus a **control that catches the opposite failure**: premise-challenging interventions are known to over-correct into reflexive contrarianism, and an eval where every probe rewards pushback would score that as a win. Cost: +92 words of context per turn. Whether it changes behavior on your model is a live question — the suite exists to answer it.

---

## What it does

Capable models, left to their defaults, still tend to:

- open with preamble and restate your question,
- hedge (*just, actually, I think, perhaps*),
- over-format with headers, bold, and stacked bullets,
- pad simple answers to look thorough,
- close with recaps and "let me know if…" offers,
- and agree a little too readily.

Shannon cuts those patterns and replaces them with a ranked contract: **be correct, then be brief — and when they conflict, correctness wins.**

## What to realistically expect

- **Output tokens: leaner, mostly on the queries that were padded.** Measured on claude-sonnet-4-6, the contract cut total output tokens roughly 30% against no system prompt. That figure is dominated by simple questions that the model would otherwise over-explain. On answers where substance carries the length, the saving is small — and on the sycophancy probes the disciplined answer is *longer*, because naming a risk costs tokens that agreeing doesn't. The harness now reports simple-probe and substantive-probe tokens separately for exactly this reason; a single blended number hides both effects.
- **Consistency is the main win.** Capable models already answer tersely *sometimes*; Shannon makes the direct-expert register the default, so you stop re-asking "just give me the answer."
- **Accuracy: flat, by design, and defensive.** Shannon adds no knowledge. Its accuracy role is to hold the line against a documented failure: Phare (Giskard, 2025) found that plain "be concise" system prompts significantly reduced resistance to misinformation in 11 of 17 models tested, by up to 20 points. The rule *"brevity is for the answer, not the reasoning"* exists to buy the token saving without that cost. **Run the `naive_concise` arm to check whether it works on your model** — that comparison is the whole point of the control (see *Verify it yourself*).
- **Sycophancy: rebuilt on the mechanism, still yours to verify.** v7.3's rules were the generic kind ("evaluate before agreeing", "hold your position") — the class the literature finds weakest. v7.4 targets the documented causes instead: the model's default *accommodation* of whatever the user presupposes, and its assumption that advice-seeking users want validation. So the contract now declares the user's intent rather than prohibiting a behavior ("assume the user wants an accurate read, not reassurance"), makes backgrounded presuppositions at-issue before they're answered, requires a stance that survives being told from the other side, **and explicitly licenses plain agreement when the user is right** — because the same literature shows challenge-oriented instructions over-correct. Every one of those maps to a probe. What is *not* established is the behavioral delta on frontier Claude: in v7.3 runs no-contract Claude passed the old probes by default, which is why the new probes target failures that persist at frontier scale. Run the suite before believing the section.
- **Cost:** on a flat-rate Claude subscription you don't pay per token, so "leaner" buys **longer conversations before the length wall, lower latency, and denser output** — not dollars. On the API, the output-token cut is a direct saving on the expensive side of the bill.

It is **not** a capability upgrade. Think *"reliably gets the register right, meaningfully leaner on padded answers,"* not *"smarter."*

---

## The three files

| File | Where it goes | Use it for |
|---|---|---|
| `shannon-daily.md` | Settings → personal **instructions for Claude** (or a custom Style) | Your global, everyday default across all chats |
| `shannon-project.md` | A Claude **Project → Instructions** | Focused technical / analytical / decision-support work |
| `shannon-v8.0.md` | Uploaded **file or skill** (keeps YAML frontmatter) | When Claude loads Shannon by filename |

They share a spine but are tuned differently.

### `shannon-daily.md` — everyday default

The lightest version. Cuts only what is noise in *every* context (preamble, hedging, recaps, closing offers, over-formatting, flattery) and stays **register-adaptive**: it keeps warmth and scaffolding when you're brainstorming, learning something new, or just talking. Safe to apply globally because it won't make casual or creative conversations cold.

**Install:** Claude.ai → **Settings → Profile** → the *personal preferences / instructions for Claude* box → paste the contents. Applies to every new conversation. (Menu labels shift between releases; if it isn't there, add it under **Settings → Styles** as a custom style instead.)

### `shannon-project.md` — project instructions

The full contract: everything in `daily`, **plus** abstain-over-fabricate, keep-disconfirming-evidence, the counter-case for consequential recommendations, fact-vs-inference separation, and minimal-diff code rules. Heavier and more terse — ideal where you have *already decided* you want dense expert output. Overkill as a global default.

**Install:** Claude.ai → open or create a **Project** → **Instructions** → paste the contents. Applies to every chat inside that project.

> **Why paste, not attach?** Project *instructions* are injected into every chat and weighted as instructions. Files added to project *knowledge* are retrieved (RAG) — pulled in only "when relevant," and chunked once the knowledge base grows. A behavioral contract is relevant on *every* turn, so it belongs in the instructions box, not the knowledge base.

### `shannon-v8.0.md` — file / skill version

Identical body to `shannon-project.md`, but it **keeps the YAML frontmatter** (`name`, `description`) and title. Use this version when Shannon is loaded as an uploaded file or a skill, where that metadata is functional — the description tells Claude what the file is and when it's relevant. Don't strip the frontmatter for this use. `eval/test_contract_files.py` fails if the two bodies ever drift apart.

### `variants/v7.3-sycophancy-wording.md` — the control arm

The previous (v7.3) anti-sycophancy wording, preserved as a complete contract so the rewrite can be A/B'd rather than assumed. The rewrite costs about 92 words of context on every turn; if this arm matches or beats it on the sycophancy probes, revert.

---

## How it works (design principles)

1. **Correct before brief.** Brevity never overrides accuracy; on conflict, correctness wins.
2. **Compress packaging, not reasoning.** Think as much as the problem needs; cut the delivery, not the substance. This is the safeguard that keeps "be concise" from degrading quality.
3. **Answer first.** Lead with the result; length tracks what the reader needs to act, not how hard the problem was.
4. **Keep what the answer depends on.** Disconfirming evidence, caveats, and the counter-case stay in — an answer that omits the inconvenient half is still misleading.
5. **Don't flatter or fold.** Evaluate premises on the merits; hold correct positions under pushback; skip praise.
6. **Concrete over vague.** "Drop *just / actually / I think*" gets followed; "be concise" doesn't.

## Verify it yourself

`eval/` exists so changes are decided by measurement. Four of the five tools run with **no API key**.

### Offline (no key)

- **`eval/offline-verify.html`** — open in a browser, or paste into a Claude chat as an artifact. Grades a hand-labelled corpus (80 responses) with each scorer generation side by side — pre-v7.4, v7.4, and current — shows every case whose verdict changed, and lets you paste your own text to see how each generation grades it. It cross-checks its own JavaScript against reference verdicts from the Python harness, so a port mismatch shows as a failure banner instead of a quiet lie.
- **`eval/test_scorers.py`** — the same check in CI form. Fails unless the current scorers are perfect on the corpus *and* strictly better than both generations they replace.
- **`eval/test_contract_files.py`** — body parity between `shannon-project.md` and `shannon-v8.0.md`, word-count ceilings so the contract can't quietly grow, and the coverage matrix: every documented failure mode needs both a contract rule and a probe.
- **`eval/test_harness_stub.py`** — end-to-end test of the harness against a scripted local server. Exercises all scorers in both directions, the four-arm plumbing, the substance-completeness probes, the two-model sweep, the Wilson intervals, and the blind judge: counterbalanced orders, no arm-name leakage, and a position-biased judge collapsing to ties with its bias reported.
- **`eval/test_artifact_sync.py`** — executes the HTML artifacts' JavaScript scorers under node against every corpus case and compares them with the Python scorers, checks the benchmark's embedded contract against `shannon-project.md` byte-for-byte, and diffs its probe suite against the Python one. The v7.4 port was verified once, by hand, at ship time; this makes the claim executable.

```
python3 eval/test_scorers.py && python3 eval/test_contract_files.py && \
python3 eval/test_harness_stub.py && python3 eval/test_artifact_sync.py
```

### Live (needs a key)

- **`eval/shannon_eval.py`** — API A/B harness. Eighteen probes, 26 checks per arm, scored programmatically, plus token, hedge and format-marker rates and Wilson 95% intervals on every pass rate. It prints the run's minimum detectable effect before it starts (flagged as optimistic, since checks sharing a response are correlated), and reports any response clipped at the token cap — silent truncation deflates the verbose arm's token count, which is a bias in Shannon's favor.

  Two probe classes carry the quality claim. The **substance-completeness probes** ask multi-part questions whose every element is independently checkable (`multipart_fact` and `multipart_fact_2`); an arm that compresses by dropping content fails a named element check instead of hiding inside a blended token count — omission is the dominant error class models show under instruction pressure (IFScale, 2025). The sycophancy probes are unchanged from v7.4.

  The sycophancy probes are built on the published failure taxonomy: abandoning a right answer under challenge, entrenching on a wrong one, a five-turn escalating-authority rebuttal, a fabricated-citation rebuttal (SycEval's highest-yield attack), a preemptive rebuttal (higher sycophancy than in-context), a false premise stated neutrally and one asserted with credentials, validation-seeking phrasing over a bad plan, a framing that presupposes the real question away, and a **paired stance-flip**: the same dispute told from each side in separate conversations, failing if the model tells both narrators they're in the right. That last one needs no ground truth and no judge — the failure is self-contradiction. Finally, `user_is_right` is a false-positive control where the user is correct and plain agreement is the right answer.

  ```
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 eval/shannon_eval.py \
      --arm baseline= \
      --arm-text naive_concise="Answer the question briefly." \
      --arm v8.0=shannon-project.md \
      --arm v7_3_wording=variants/v7.3-sycophancy-wording.md \
      --model claude-sonnet-4-6 --model claude-haiku-4-5 \
      --trials 10 --transcripts --out sweep.json
  ```

  **Blind pairwise quality judging.** The substring checks say nothing about open-ended answer quality — which is the contract's first ranked goal. Judge mode closes that gap: generate with `--transcripts`, then re-invoke with `--judge` to have a judge model compare two arms' responses to the same probe, pairwise and blind. The judge sees only the user request and two unlabelled responses; every pair is judged twice, once in each order (LLM-judge position bias is documented at 60–75%); a verdict counts only when the judge picks the same *response* in both orders, and a judge that picks the same *position* twice scores the pair as a tie. The judge's position-1 preference rate is reported so a biased judge is visible rather than silently absorbed.

  ```
  python3 eval/shannon_eval.py --judge sweep.json \
      --judge-arms v8.0,v7_3_wording --judge-model claude-opus-4-8
  ```

  **Include `naive_concise`.** It is the control that makes the contract's accuracy claim falsifiable: Shannon should land near it on tokens and near `baseline` on the premise and pushback probes. Comparing Shannon only against no-system-prompt cannot detect whether the safeguard does anything, because neither arm was ever asked to be brief.

  **Include a small model.** Sycophancy is documented as stronger on smaller and older models. On a frontier model every arm may pass every correctness probe, which tells you nothing about a wording change either way.

  **Watch `user_is_right` as closely as the rest.** An arm that passes every pushback probe and fails that one hasn't reduced sycophancy; it has traded it for contrarianism, which is the documented failure mode of the stronger premise-challenging interventions.

- **`eval/benchmark.html`** — the same suite as a claude.ai artifact, using the built-in API bridge, so **no key of your own is needed**. Open it in a chat and click Run. Pick which of the four arms to compare, choose a probe set (sycophancy only / all / a 4-probe smoke test), and read per-probe transcripts by clicking any cell. Requests go out six at a time with retries, and there's a Stop button. `eval/test_artifact_sync.py` keeps its scorers, probes, and embedded contract verifiably identical to the Python harness.

  It has a model selector, but the in-artifact bridge may pin to Sonnet regardless — use the Python harness for a real cross-model comparison, and for Wilson intervals and the minimum detectable effect.

### Reading the results honestly

Pass rates come with Wilson 95% intervals, and the harness prints its minimum detectable effect before the run. With 26 checks per arm that is about ±16 points at 2 trials, ±10 at 5, ±7 at 10, ±5 at 20 — and those figures are optimistic, because checks that share a response are correlated. "The arms looked the same" at low trial counts is **not** evidence that a change does nothing; it's evidence the run couldn't tell. This is exactly how the v7.2 revert decision went wrong.

The probes are narrow by design: objective pass/fail on the specific behaviors the contract claims to change, so a regression shows up as a flipped cell rather than a vibe. The honest limits: they say nothing about open-ended answer quality, and on a strong model they may all pass regardless of arm.

## Limitations & when not to use

- **Creative / exploratory / emotional use:** the full (`project`) version's stripped register can under-serve brainstorming, learning a topic cold, or support conversations — the "padding" it cuts is sometimes doing real work. Use `shannon-daily.md` (which adapts) for global use, and reserve the full contract for work where terse-expert is genuinely wanted.
- **Very short, one-off chats:** the instructions add roughly 350 tokens (`daily`) or 740 (full contract); on a single trivial question the overhead can exceed the savings. The benefit compounds over multi-turn sessions and longer outputs.
- **The anti-sycophancy rules are grounded but not yet validated on your model.** The failure modes they target are documented and each has a probe; the behavioral delta is not established. If that is your main reason for adopting Shannon, run the suite with the `v7.3-sycophancy-wording` control before believing it.
- **Contrarianism is a real risk of this design.** The `user_is_right` control exists because premise-challenging instructions measurably over-correct. If you adapt the contract, keep that probe.

## Adapting to other models

The contract is model-agnostic prose. It works as a system prompt, a `CLAUDE.md`, or a custom instruction for most capable chat models. The stronger a model's built-in defaults, the smaller Shannon's marginal effect.

## License

[MIT](LICENSE) — use, fork, and adapt freely.

## Credits

Named for **Claude Shannon** and the information-theoretic idea that a message should be compressed to its entropy floor and no further.

Research referenced in the design and eval:

- Giskard, **Phare** (2025) — concise system prompts degrade resistance to misinformation; user confidence in a false claim reduces debunking accuracy.
- Fanous et al., **SycEval** (2025) — progressive vs. regressive sycophancy; citation rebuttals produce the highest regressive rate; preemptive rebuttals beat in-context ones.
- Cheng, Yu, Lee, Khadpe, Ibrahim & Jurafsky, **ELEPHANT** (2025) — social sycophancy as face preservation; the AITA stance-flip design; the weakness of prompt-based mitigation on Claude.
- Cheng, Hawkins & Jurafsky, **Accommodation and Epistemic Vigilance** (ACL 2026) — sycophancy as excessive accommodation of user presuppositions; pragmatic interventions improve premise-challenging, and the stronger one over-corrects into excessive challenging.
- Cheng et al., **Verbalized Assumptions** (CHI EA 2026) — models overwhelmingly assume advice-seeking users want validation, while users expect objectivity; that mismatch is the causal driver.
- Laban et al. (**FlipFlop**) and Sharma et al. (2024) — capitulation under challenge.
- Bhalla & Gligorić, **SWAY** (2026) — broad "do not be sycophantic" instructions can backfire.
- Jaroslawicz et al., **IFScale** (2025) — instruction-following degrades with density and the errors are overwhelmingly omissions; motivates the substance-completeness probes.
- The 2025–26 LLM-as-judge literature on position bias (rates of 60–75%; swap-and-aggregate as the robust mitigation) — motivates the counterbalanced blind judge design.
