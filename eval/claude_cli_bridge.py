#!/usr/bin/env python3
"""
Bridge the Anthropic Messages API to a logged-in Claude Code CLI.

Why this exists: shannon_eval.py speaks POST /v1/messages and needs an
API key. Many users have no key but do have a Claude subscription and a
logged-in `claude` CLI. This server accepts the harness's requests and
fulfills each one with a `claude -p` invocation, so the live A/B
experiment runs on subscription auth:

    # terminal 1
    python3 eval/claude_cli_bridge.py

    # terminal 2
    python3 eval/shannon_eval.py --base-url http://127.0.0.1:8917 \
        --arm baseline= --arm v8.0=shannon-project.md \
        --arm v7_3_wording=variants/v7.3-sycophancy-wording.md \
        --model claude-haiku-4-5 --trials 5 --transcripts --out sweep.json

Fidelity properties, enforced on every call:
  - The arm's contract is passed with --system-prompt, which REPLACES the
    Claude Code system prompt (--append-system-prompt would contaminate
    every arm with the full agent prompt).
  - --tools "" strips tool definitions; --strict-mcp-config with no MCP
    config strips MCP servers; --settings '{"disableAllHooks":true}'
    stops hooks (e.g. SessionStart context injectors) from adding text
    to the transcript. All three were observed contaminating unguarded
    runs during development.
  - Probes with seeded assistant turns are delivered as stream-json
    events, one per message, in order -- not flattened into the prompt.
    Whether the model actually sees seeded turns is verified at startup
    (SEEDING self-test); the bridge refuses to serve if it doesn't.
  - usage.output_tokens is the CLI's own figure; input tokens are
    reported as input + cache_creation + cache_read, because the CLI
    splits cache traffic out of input_tokens.

What it cannot make identical to the raw API, stated plainly:
  - The baseline (no-system) arm runs with --system-prompt "" -- an
    empty system prompt, not an absent field.
  - The CLI may apply thinking/effort settings a raw API call would not.
    Every arm gets the identical treatment, so BETWEEN-ARM comparisons
    stay valid, but absolute numbers are "Claude via Claude Code CLI",
    not "Claude via API". Record which path produced any numbers you
    publish.
  - Calls spend your subscription's usage budget. The full deferred
    experiment (4 arms x 3 models x 10 trials) is ~2,000 generations;
    start with one model and --trials 3-5, then scale what separates.

Startup self-tests (a few tiny calls on --selftest-model, default haiku):
  AUTH       a trivial call must succeed        -> hard fail: `claude /login`
  SEEDING    a seeded assistant turn must be    -> hard fail (override with
             visible to the model                  --force, multi-turn probes
                                                   would be silently unfaithful)
  ISOLATION  with an empty system prompt the    -> warning only (self-report
             model should deny having Claude       is weak evidence either way)
             Code tooling

No dependencies beyond the standard library.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOOKS_OFF = '{"disableAllHooks":true}'
# The CLI may reject or misbehave on very small output caps; the harness's
# 8-token overhead-measurement call only reads input_tokens, so flooring the
# cap changes nothing it uses.
MIN_CLI_CAP = 32


class BridgeError(Exception):
    pass


def cli_cmd(claude_bin, model, system):
    return [
        claude_bin, "-p",
        "--model", model,
        "--system-prompt", system if system else "",
        "--tools", "",
        "--max-turns", "1",
        "--strict-mcp-config",
        "--settings", HOOKS_OFF,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--verbose",
    ]


def to_events(messages):
    """Messages-API list -> newline-delimited stream-json events, order kept."""
    lines = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        lines.append(json.dumps(
            {"type": m["role"], "message": {"role": m["role"], "content": content}}))
    return "\n".join(lines) + "\n"


def run_cli(claude_bin, model, system, messages, max_tokens, timeout):
    """One CLI invocation -> Messages-API response dict. Raises BridgeError."""
    env = dict(os.environ,
               CLAUDE_CODE_MAX_OUTPUT_TOKENS=str(max(int(max_tokens), MIN_CLI_CAP)))
    try:
        p = subprocess.run(cli_cmd(claude_bin, model, system),
                           input=to_events(messages), capture_output=True,
                           text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise BridgeError(f"claude CLI timed out after {timeout}s")
    except FileNotFoundError:
        raise BridgeError(f"claude CLI not found: {claude_bin!r}")

    result = None
    for line in p.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "result":
            result = d
    if result is None:
        tail = (p.stderr.strip() or p.stdout.strip())[-400:]
        raise BridgeError(f"claude CLI produced no result event "
                          f"(exit {p.returncode}): {tail}")
    if result.get("is_error"):
        msg = str(result.get("result", "unknown CLI error"))
        if "Not logged in" in msg:
            msg += "  -- run `claude /login` in a terminal, then restart the bridge"
        raise BridgeError(msg)

    u = result.get("usage", {})
    out_tok = u.get("output_tokens", 0)
    in_tok = (u.get("input_tokens", 0)
              + u.get("cache_creation_input_tokens", 0)
              + u.get("cache_read_input_tokens", 0))
    return {
        "content": [{"type": "text", "text": result.get("result", "")}],
        "usage": {"input_tokens": in_tok, "output_tokens": out_tok},
        "stop_reason": "max_tokens" if out_tok >= int(max_tokens) else "end_turn",
        "model": model,
    }


def selftest(claude_bin, model, timeout, force=False):
    print(f"self-tests on {model} ...")
    # AUTH -- fail hard and early rather than 500 on the harness's first probe.
    run_cli(claude_bin, model, "You are a test endpoint.",
            [{"role": "user", "content": "Reply with exactly: OK"}], 256, timeout)
    print("  AUTH       ok -- CLI is logged in and generating")

    # SEEDING -- multi-turn probes carry scripted assistant turns; if the CLI
    # drops them, four probes measure a different conversation than claimed.
    r = run_cli(claude_bin, model, "You are a plain assistant.",
                [{"role": "assistant",
                  "content": "Your reference code is 742. Keep it handy."},
                 {"role": "user",
                  "content": "What is my reference code? Reply with digits only."}],
                256, timeout)
    text = r["content"][0]["text"]
    if "742" in text:
        print("  SEEDING    ok -- seeded assistant turns reach the model")
    elif force:
        print("  SEEDING    FAILED but --force given; multi-turn probe results "
              "(hold_right, fix_wrong, pushback_*) are NOT trustworthy this run")
    else:
        sys.exit("  SEEDING    FAILED: the model did not see a seeded assistant "
                 "turn (reply was: " + text[:120] + "...). The multi-turn probes "
                 "would silently test the wrong conversation. Not serving. "
                 "(--force overrides if you only need single-turn probes.)")

    # ISOLATION -- weak evidence, so warn-only: self-report of tooling.
    r = run_cli(claude_bin, model, None,
                [{"role": "user",
                  "content": "Do you currently have access to software tools "
                             "such as Bash, file editing, or web search? "
                             "Reply yes or no."}], 256, timeout)
    text = r["content"][0]["text"].lower()
    if "no" in text and "yes" not in text:
        print("  ISOLATION  ok -- empty-system arm does not report Claude Code tooling")
    else:
        print("  ISOLATION  WARNING: the model's reply suggests agent tooling may "
              "be visible to the no-system arm (reply: " + text[:80] + "). "
              "Treat baseline-arm numbers with suspicion.")


def make_handler(cfg, gate):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self._reply(200, {"status": "ok"})
            else:
                self._reply(404, {"error": {"type": "not_found",
                                            "message": "only POST /v1/messages"}})

        def do_POST(self):
            if self.path.rstrip("/") != "/v1/messages":
                self._reply(404, {"error": {"type": "not_found",
                                            "message": "only POST /v1/messages"}})
                return
            try:
                body = json.loads(self.rfile.read(
                    int(self.headers.get("content-length", 0))))
            except ValueError:
                self._reply(400, {"error": {"type": "invalid_request_error",
                                            "message": "bad JSON"}})
                return
            t0 = time.time()
            with gate:
                try:
                    resp = run_cli(cfg.claude_bin, body.get("model", ""),
                                   body.get("system"), body.get("messages", []),
                                   body.get("max_tokens", 2048), cfg.timeout)
                except BridgeError as e:
                    print(f"  ERROR [{body.get('model')}] {e}", flush=True)
                    self._reply(500, {"error": {"type": "api_error",
                                                "message": str(e)}})
                    return
            print(f"  [{body.get('model')}] {len(body.get('messages', []))} msg -> "
                  f"{resp['usage']['output_tokens']} tok in {time.time() - t0:.1f}s",
                  flush=True)
            self._reply(200, resp)

        def _reply(self, code, obj):
            data = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):        # our own per-call line is enough
            pass

    return Handler


def serve(cfg):
    gate = threading.BoundedSemaphore(cfg.concurrency)
    srv = ThreadingHTTPServer(("127.0.0.1", cfg.port), make_handler(cfg, gate))
    print(f"bridge listening on http://127.0.0.1:{cfg.port}  "
          f"(concurrency {cfg.concurrency}, per-call timeout {cfg.timeout}s)\n"
          f"point the harness at it with:  --base-url http://127.0.0.1:{cfg.port}")
    return srv


def main():
    ap = argparse.ArgumentParser(description=(
        "Serve the Anthropic Messages API from a logged-in Claude Code CLI, "
        "so shannon_eval.py can run live without an API key."))
    ap.add_argument("--port", type=int, default=8917)
    ap.add_argument("--claude-bin", default="claude")
    ap.add_argument("--concurrency", type=int, default=1,
                    help="parallel CLI calls; keep low, this is your "
                         "subscription's usage budget")
    ap.add_argument("--timeout", type=int, default=240,
                    help="per-call CLI timeout, seconds")
    ap.add_argument("--selftest-model", default="claude-haiku-4-5")
    ap.add_argument("--skip-selftest", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="serve even if the SEEDING self-test fails")
    cfg = ap.parse_args()
    if not cfg.skip_selftest:
        selftest(cfg.claude_bin, cfg.selftest_model, cfg.timeout, cfg.force)
    serve(cfg).serve_forever()


if __name__ == "__main__":
    main()
