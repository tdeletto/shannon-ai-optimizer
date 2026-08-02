#!/usr/bin/env python3
"""
Offline verification of claude_cli_bridge.py against a mock `claude` CLI.

The bridge's live behavior depends on a logged-in CLI, which CI does not
have. What CAN be verified offline, and is here:

  1. Invocation fidelity -- every CLI call carries the flags the bridge's
     isolation guarantees depend on: --system-prompt (replace, not append),
     --tools "", --strict-mcp-config, hooks disabled, stream-json in/out,
     --max-turns 1.
  2. Message translation -- seeded assistant turns arrive as ordered
     stream-json events with roles intact; string content is wrapped to
     block form; the no-system arm maps to --system-prompt "".
  3. Response translation -- CLI result events map to the Messages-API
     shape shannon_eval.call_api() parses: text joined from content,
     input tokens summed across the CLI's cache split, stop_reason
     inferred against the requested cap.
  4. Self-test gating -- AUTH failure refuses to serve; SEEDING failure
     refuses without --force.
  5. End-to-end -- the real harness, pointed at the bridge over HTTP,
     completes a full 2-arm run and writes well-formed results JSON.

What this cannot verify, stated plainly: that the real CLI honors the
same contract the mock implements (seeded turns reaching the model, the
empty system prompt actually replacing the agent prompt). That is what
the bridge's startup self-tests are for -- they run the same checks
against the real CLI before it serves a single probe.
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import claude_cli_bridge as bridge       # noqa: E402
import shannon_eval as se                # noqa: E402

TMP = tempfile.mkdtemp(prefix="shannon_bridge_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
MOCK_LOG = os.path.join(TMP, "mock_log.jsonl")

MOCK_CLI = r'''#!/usr/bin/env python3
import json, os, sys
argv = sys.argv[1:]
events = [json.loads(l) for l in sys.stdin if l.strip()]

def flag(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

with open(os.environ["MOCK_LOG"], "a") as f:
    f.write(json.dumps({"argv": argv,
                        "roles": [e.get("type") for e in events],
                        "env_cap": os.environ.get("CLAUDE_CODE_MAX_OUTPUT_TOKENS")}) + "\n")

mode = os.environ.get("MOCK_MODE", "ok")
sysprompt = flag("--system-prompt", "<missing>")
users = [e for e in events if e.get("type") == "user"]
seeded = [e for e in events if e.get("type") == "assistant"]
last_user = users[-1]["message"]["content"][0]["text"] if users else ""

if mode == "logged_out":
    d = {"type": "result", "subtype": "success", "is_error": True,
         "result": "Not logged in · Please run /login",
         "usage": {"input_tokens": 0, "output_tokens": 0}}
elif mode == "no_seeding" and "reference code" in last_user:
    d = {"type": "result", "subtype": "success", "is_error": False,
         "result": "I have not given you any reference code.",
         "usage": {"input_tokens": 10, "output_tokens": 8}}
else:
    if "reference code" in last_user:
        text = "742"
    elif "software tools" in last_user:
        text = "No."
    elif last_user == "Reply with exactly: OK":
        text = "OK"
    else:
        seed = seeded[0]["message"]["content"][0]["text"][:24] if seeded else ""
        text = "SYS<%s> SEED<%s> ANS" % (sysprompt[:32], seed)
    d = {"type": "result", "subtype": "success", "is_error": False,
         "result": text,
         "usage": {"input_tokens": 100, "cache_creation_input_tokens": 30,
                   "cache_read_input_tokens": 20, "output_tokens": 7}}

print(json.dumps({"type": "system", "subtype": "init"}))
print("plain non-JSON noise the parser must skip")
print(json.dumps(d))
'''


def write_mock():
    path = os.path.join(TMP, "claude")
    with open(path, "w") as f:
        f.write(MOCK_CLI)
    os.chmod(path, 0o755)
    return path


def mock_calls():
    if not os.path.exists(MOCK_LOG):
        return []
    return [json.loads(l) for l in open(MOCK_LOG)]


def clear_log():
    open(MOCK_LOG, "w").close()


def main():
    os.environ["MOCK_LOG"] = MOCK_LOG
    os.environ.pop("MOCK_MODE", None)
    mock = write_mock()
    failures = []

    def check(cond, label):
        print(("  ok   " if cond else "  FAIL ") + label)
        if not cond:
            failures.append(label)

    # ---- 1+2+3: translation fidelity through run_cli ----------------------
    clear_log()
    r = bridge.run_cli(mock, "claude-test-1", "CONTRACT BODY HERE",
                       [{"role": "user", "content": "hello"}], 2048, 30)
    call = mock_calls()[-1]
    argv = call["argv"]
    check("--system-prompt" in argv
          and argv[argv.index("--system-prompt") + 1] == "CONTRACT BODY HERE",
          "system prompt passed via --system-prompt (replace, not append)")
    check("--append-system-prompt" not in argv, "no --append-system-prompt")
    check("--tools" in argv and argv[argv.index("--tools") + 1] == "",
          "tool definitions stripped (--tools \"\")")
    check("--strict-mcp-config" in argv, "MCP servers stripped")
    check(bridge.HOOKS_OFF in argv, "hooks disabled via --settings")
    check("--max-turns" in argv and argv[argv.index("--max-turns") + 1] == "1",
          "agentic loop capped at one turn")
    check(argv[argv.index("--model") + 1] == "claude-test-1", "model passthrough")
    check(call["roles"] == ["user"], "single-turn -> one user event")
    check(call["env_cap"] == "2048", "max_tokens -> CLAUDE_CODE_MAX_OUTPUT_TOKENS")
    check(r["content"][0]["text"].startswith("SYS<CONTRACT BODY HERE"),
          "response text surfaces from the result event")
    check(r["usage"]["input_tokens"] == 150,
          "input tokens = input + cache_creation + cache_read")
    check(r["usage"]["output_tokens"] == 7 and r["stop_reason"] == "end_turn",
          "output tokens + end_turn under the cap")

    clear_log()
    msgs = [{"role": "user", "content": "u1"},
            {"role": "assistant", "content": "seeded stance"},
            {"role": "user", "content": "u2"}]
    r = bridge.run_cli(mock, "claude-test-1", "S", msgs, 2048, 30)
    check(mock_calls()[-1]["roles"] == ["user", "assistant", "user"],
          "seeded assistant turns delivered as ordered events")
    check("SEED<seeded stance>" in r["content"][0]["text"],
          "seeded content visible to the (mock) model")

    clear_log()
    bridge.run_cli(mock, "claude-test-1", None,
                   [{"role": "user", "content": "u"}], 8, 30)
    call = mock_calls()[-1]
    argv = call["argv"]
    check(argv[argv.index("--system-prompt") + 1] == "",
          "no-system arm -> --system-prompt \"\" (never the agent prompt)")
    check(call["env_cap"] == str(bridge.MIN_CLI_CAP),
          "tiny caps floored to MIN_CLI_CAP for the CLI")

    clear_log()
    r = bridge.run_cli(mock, "claude-test-1", "S",
                       [{"role": "user", "content": "u"}], 7, 30)
    check(r["stop_reason"] == "max_tokens",
          "stop_reason max_tokens when output reaches the requested cap")

    # ---- 4: self-test gating ---------------------------------------------
    os.environ["MOCK_MODE"] = "logged_out"
    try:
        bridge.selftest(mock, "claude-test-1", 30)
        check(False, "AUTH gate: selftest must raise when CLI is logged out")
    except (bridge.BridgeError, SystemExit):
        check(True, "AUTH gate: logged-out CLI refuses to serve")

    os.environ["MOCK_MODE"] = "no_seeding"
    try:
        bridge.selftest(mock, "claude-test-1", 30)
        check(False, "SEEDING gate: selftest must exit when seeding fails")
    except SystemExit:
        check(True, "SEEDING gate: dropped seeded turns refuse to serve")
    bridge.selftest(mock, "claude-test-1", 30, force=True)
    check(True, "SEEDING gate: --force overrides with a warning")

    os.environ.pop("MOCK_MODE", None)
    bridge.selftest(mock, "claude-test-1", 30)
    check(True, "selftest passes against a well-behaved CLI")

    # ---- 5: end-to-end through the real harness over HTTP ----------------
    cfg = types.SimpleNamespace(claude_bin=mock, port=0, concurrency=2, timeout=60)
    srv = bridge.serve(cfg)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health") as resp:
        check(json.load(resp)["status"] == "ok", "health endpoint")

    text, out_tok, in_tok, stop = se.call_api(
        f"http://127.0.0.1:{port}", "", "claude-test-1", "SYSTEM X",
        [{"role": "user", "content": "via call_api"}])
    check(text.startswith("SYS<SYSTEM X") and out_tok == 7 and in_tok == 150
          and stop == "end_turn",
          "shannon_eval.call_api parses bridge responses end-to-end")

    os.environ["MOCK_MODE"] = "logged_out"
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/messages",
        data=json.dumps({"model": "m", "max_tokens": 64,
                         "messages": [{"role": "user", "content": "u"}]}).encode(),
        headers={"content-type": "application/json"})
    try:
        urllib.request.urlopen(req)
        check(False, "CLI errors must surface as HTTP 500")
    except urllib.error.HTTPError as e:
        body = json.load(e)
        check(e.code == 500 and "logged in" in body["error"]["message"],
              "CLI errors surface as HTTP 500 with the CLI's message")
    os.environ.pop("MOCK_MODE", None)

    out_json = os.path.join(TMP, "e2e.json")
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "shannon_eval.py"),
         "--base-url", f"http://127.0.0.1:{port}",
         "--arm", "baseline=", "--arm", "shannon=shannon-project.md",
         "--model", "claude-test-1", "--trials", "1", "--out", out_json],
        capture_output=True, text=True, cwd=ROOT,
        env=dict(os.environ, MOCK_LOG=MOCK_LOG))
    check(r.returncode == 0,
          f"full harness run against the bridge exits 0 "
          f"(stderr tail: {r.stderr.strip()[-200:] or 'none'})")
    if r.returncode == 0:
        data = json.load(open(out_json))
        arms = data["models"]["claude-test-1"]["arms"]
        check(set(arms) == {"baseline", "shannon"},
              "results JSON carries both arms")
        n_calls = sum(1 for c in mock_calls())
        check(n_calls >= 2 * len(se.PROBES),
              f"one CLI call per probe per arm reached the mock ({n_calls})")
    srv.shutdown()

    print()
    if failures:
        for f in failures:
            print("FAIL:", f)
        sys.exit(1)
    print("ALL BRIDGE ASSERTIONS PASSED -- invocation flags, message and "
          "response translation, self-test gating, and a full harness run "
          "over HTTP against the mock CLI.")


if __name__ == "__main__":
    main()
