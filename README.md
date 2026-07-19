# Shannon — AI Optimizer

> Maximum signal per token. Compress the packaging, never the content.

Shannon is a small set of operating instructions for Claude (adaptable to other capable LLMs) that make responses **leaner, more direct, and less sycophantic** — without cutting the reasoning, caveats, or accuracy that answers depend on.

It's named after **Claude Shannon**, founder of information theory. The goal is to push every response toward its *entropy floor*: strip the tokens that carry no information, keep every token correctness needs.

Current version: **v7.3**.

> **v7.3 = the v7.1 contract text + the evaluation suite.** v7.2 experimented with rewording the pushback rule and a few others; measured against no-contract and v7.1 on claude-sonnet-4-6, those changes showed no correctness benefit and cost tokens, so the contract was reverted. What v7.3 keeps from that work is `eval/` — a real A/B harness, an in-chat benchmark, and a multi-model sweep — so the next change has to *earn its way in* with numbers. The v7.2 wording is preserved in `CHANGELOG.md` and git history for anyone testing on weaker/older models, where its logical fixes may still matter.

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

Measured on claude-sonnet-4-6 (2 trials/probe, 8 probes, via `eval/`): the contract cut total output tokens ~31% vs no contract (2693 → ~1860) and roughly halved hedge density, with no drop on any correctness/sycophancy check. On that model the correctness probes did not separate the contract from no-contract — it already passes them by default — so the token and formatting wins are the reliable gains there. Run the eval on your own model before assuming the numbers transfer.


Honest calibration, not hype:

- **Output tokens:** roughly **15–30% leaner** on a mixed workload — more on simple/over-explained queries, less on long tasks where substance dominates. Your query mix is the biggest variable.
- **Consistency** is the main win. Capable models already answer tersely *sometimes*; Shannon makes the direct-expert register the default, so you stop re-asking "just give me the answer."
- **Accuracy:** roughly **flat, by design.** Shannon adds no knowledge. Its accuracy role is defensive — a built-in rule (*"brevity is for the answer, not the reasoning"*) guards against the documented failure where "be concise" instructions *raise* hallucination by starving the reasoning. It holds accuracy steady while cutting tokens; it does not boost it.
- **Sycophancy:** reduced, via explicit rules to evaluate premises, hold correct positions under pushback, and skip flattery.
- **Cost:** on a flat-rate Claude subscription you don't pay per token, so "leaner" buys **longer conversations before the length wall, lower latency, and denser output** — not dollars. On the API, the output-token cut is a direct saving on the expensive side of the bill.

It is **not** a capability upgrade. Think *"reliably gets the register right, ~15–30% leaner, less flattery,"* not *"smarter."*

---

## The three files

| File | Where it goes | Use it for |
|---|---|---|
| `shannon-daily.md` | Settings → personal **instructions for Claude** (or a custom Style) | Your global, everyday default across all chats |
| `shannon-project.md` | A Claude **Project → Instructions** | Focused technical / analytical / decision-support work |
| `shannon-v7.3.md` | Uploaded **file or skill** (keeps YAML frontmatter) | When Claude loads Shannon by filename |

They share a spine but are tuned differently.

### `shannon-daily.md` — everyday default

The lightest version. Cuts only what is noise in *every* context (preamble, hedging, recaps, closing offers, over-formatting, flattery) and stays **register-adaptive**: it keeps warmth and scaffolding when you're brainstorming, learning something new, or just talking. Safe to apply globally because it won't make casual or creative conversations cold.

**Install:** Claude.ai → **Settings → Profile** → the *personal preferences / instructions for Claude* box → paste the contents. Applies to every new conversation. (Menu labels shift between releases; if it isn't there, add it under **Settings → Styles** as a custom style instead.)

### `shannon-project.md` — project instructions

The full contract: everything in `daily`, **plus** abstain-over-fabricate, keep-disconfirming-evidence, the counter-case for consequential recommendations, fact-vs-inference separation, and minimal-diff code rules. Heavier and more terse — ideal where you have *already decided* you want dense expert output. Overkill as a global default.

**Install:** Claude.ai → open or create a **Project** → **Instructions** → paste the contents. Applies to every chat inside that project.

> **Why paste, not attach?** Project *instructions* are injected into every chat and weighted as instructions. Files added to project *knowledge* are retrieved (RAG) — pulled in only "when relevant," and chunked once the knowledge base grows. A behavioral contract is relevant on *every* turn, so it belongs in the instructions box, not the knowledge base.

### `shannon-v7.3.md` — file / skill version

Identical body to `shannon-project.md`, but it **keeps the YAML frontmatter** (`name`, `description`) and title. Use this version when Shannon is loaded as an uploaded file or a skill, where that metadata is functional — the description tells Claude what the file is and when it's relevant. Don't strip the frontmatter for this use.

---

## How it works (design principles)

1. **Correct before brief.** Brevity never overrides accuracy; on conflict, correctness wins.
2. **Compress packaging, not reasoning.** Think as much as the problem needs; cut the delivery, not the substance. This is the safeguard that keeps "be concise" from degrading quality.
3. **Answer first.** Lead with the result; length tracks what the reader needs to act, not how hard the problem was.
4. **Keep what the answer depends on.** Disconfirming evidence, caveats, and the counter-case stay in — an answer that omits the inconvenient half is still misleading.
5. **Don't flatter or fold.** Evaluate premises on the merits; hold correct positions under pushback; skip praise.
6. **Concrete over vague.** "Drop *just / actually / I think*" gets followed; "be concise" doesn't.

## Verify it yourself

`eval/` exists so changes are decided by measurement, not vibes:

- **`eval/shannon_eval.py`** — API A/B harness. Runs a fixed 8-probe suite (verbosity, false premises, flattery bait, and the pushback failure modes: abandoning a right answer, entrenching on a wrong one, and a 5-turn escalating-authority probe) across any arms, and scores with blunt programmatic checks plus token, hedge, and format-marker rates — no LLM judge. `--model` is **repeatable**, so you can sweep several models (Opus, Sonnet, Haiku) in one run:
  ```
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 eval/shannon_eval.py \
      --arm baseline= --arm v7.3=shannon-project.md \
      --model claude-opus-4-8 --model claude-sonnet-4-6 --model claude-haiku-4-5 \
      --trials 3 --out sweep.json
  ```
  It prints a per-model, per-arm summary table. Sycophancy is documented to be stronger on smaller/older models, so a sweep is where a wording change would show a benefit if it has one.
- **`eval/benchmark.html`** — the same suite as a claude.ai artifact (uses the built-in API bridge, no key). Paste it into a chat as an artifact and click run; compares baseline vs v7.3 with per-probe transcripts. It has a model selector, but the in-artifact bridge may pin to Sonnet regardless — use the Python harness for a real cross-model (esp. Opus) comparison.
- **`eval/test_harness_stub.py`** — offline test of the harness against a scripted local server (all scorers exercised in both directions, plus the two-model sweep plumbing). Run it before trusting harness changes.

The probes are narrow by design: they test the specific behaviors the contract claims to change, with objective pass/fail, so a regression shows up as a flipped cell rather than a vibe. The honest limit: they don't measure open-ended answer quality, and on a strong model they may all pass regardless of arm.

## Limitations & when not to use

- **Creative / exploratory / emotional use:** the full (`project`) version's stripped register can under-serve brainstorming, learning a topic cold, or support conversations — the "padding" it cuts is sometimes doing real work. Use `shannon-daily.md` (which adapts) for global use, and reserve the full contract for work where terse-expert is genuinely wanted.
- **Very short, one-off chats:** the instructions add roughly 350–450 tokens (`daily`) or 800–1,000 (full contract); on a single trivial question the overhead can exceed the savings. The benefit compounds over multi-turn sessions and longer outputs.
- **The numbers above are estimates,** not a published benchmark for your setup. To get real figures, run ~20 of your own typical prompts with and without Shannon and compare.

## Adapting to other models

The contract is model-agnostic prose. It works as a system prompt, a `CLAUDE.md`, or a custom instruction for most capable chat models. The stronger a model's built-in defaults, the smaller Shannon's marginal effect.

## License

[MIT](LICENSE) — use, fork, and adapt freely.

## Credits

Named for **Claude Shannon** and the information-theoretic idea that a message should be compressed to its entropy floor and no further.
