"""Observation run of the Agent A process-restart cases of agentproto-recovery
@ 278fbf5 (v0.2.2).

Replays the step sequence of every case in tests/test_process_restart.py
(A/B, C, D, D2, E, F, G, H, H2, I, failover, unsupported) and
tests/test_process_restart_regression.py (R1, R2) through the repo's own
tests/restart_harness.py (Cluster), WITHOUT asserting anything: every value a
step returns is recorded. Identifier values (dialog ids, incarnations, pids,
op keys) are not recorded; only codes, states, counts and the attempt suffix
of the tool's op key. No repo file is modified; the harness is imported from
the pinned tree.

usage: restart_observe.py REPO_DIR BASE_DIR OUTFILE [--repeats N]
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

ALL = ["global-store", "global-endpoint", "scoped-store", "scoped-endpoint-noticket",
       "scoped-endpoint-ticket", "scoped-endpoint-medticket"]
FAILOVER_OK = [m for m in ALL if m != "scoped-endpoint-noticket"]
REGR = ["global-store", "scoped-store", "scoped-endpoint-ticket", "scoped-endpoint-medticket"]


def strip(v):
    """Keep codes/states/outcomes; drop identifier values."""
    if isinstance(v, list):
        return [strip(x) for x in v]
    if isinstance(v, dict):
        keep = ("code", "status", "outcome", "applied", "ledger_state", "result", "detail",
                "state", "attempt", "seq", "payload")
        return {k: v[k] for k in keep if k in v}
    return v


def snap(c):
    ex = c.executions()
    out = {"a_ops": [{k: r[k] for k in ("seq", "payload", "state", "result", "attempt")}
                     for r in c.a_ops()],
           "a_next_seq": [r["next_seq"] for r in c.a_dialogs()],
           "b_ops": [{k: r[k] for k in ("seq", "state", "result", "attempt")} for r in c.b_ops()],
           "executions": len(ex),
           "exec_key_suffix": [":".join(e["op_key"].split(":")[-2:]) for e in ex]}
    try:
        out["b_fences"] = [r["fenced_through"] for r in c.b_table("op_fences")]
    except Exception:
        out["b_fences"] = None
    return out


def crash_p1(c, gate, log):
    c.ctl("arm", gate=gate)
    p1 = c.agent("P1")
    est = p1.call("establish", task="transfer")
    log.append(["P1.establish", est["code"]])
    d = est["dialog"]
    p1.send("invoke", dialog=d, payload="pay-10")
    log.append(["gate_entered:" + gate, c.ctl("wait_entered", gate=gate)])
    log.append(["A_row_before_kill", snap(c)["a_ops"]])
    log.append(["P1.sigkill_rc", p1.sigkill()])
    return p1, d


def late(c, p1):
    return strip([x["reply"] for x in c.done("invoke") if x["pid"] == p1.pid])


def p2_invokes(c, p):
    return len(c.calls("invoke", pid=p.pid))


def case_AB(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    L.append(["P2.recover", strip(p2.call("recover"))])
    L.append(["P2.unresolved", strip(p2.call("unresolved", dialog=d))])
    L.append(["snapshot", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])
    c.ctl("release", gate="tool")


def case_C(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.reconcile#1", strip(p2.call("reconcile", dialog=d))])
    L.append(["snapshot#1", snap(c)])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["late_reply_to_P1", late(c, p1)])
    L.append(["P2.reconcile#2", strip(p2.call("reconcile", dialog=d))])
    L.append(["snapshot#2", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


def case_D(c, L):
    p1, d = crash_p1(c, "pre_b", L)
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    L.append(["snapshot#1", snap(c)])
    c.ctl("release", gate="pre_b")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["late_reply_to_P1", late(c, p1)])
    L.append(["snapshot#2", snap(c)])
    L.append(["P2.retry", strip(p2.call("retry", dialog=d, seq=1))])
    L.append(["snapshot#3", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


def case_D2(c, L):
    p1, d = crash_p1(c, "tool", L)
    c.ctl("restart_b")
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["late_reply_to_P1", late(c, p1)])
    L.append(["snapshot#1", snap(c)])
    L.append(["P2.retry", strip(p2.call("retry", dialog=d, seq=1))])
    L.append(["snapshot#2", snap(c)])


def case_E(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    s0 = snap(c)
    L.append(["P2.resume#1", strip(p2.call("resume", dialog=d))])
    L.append(["P2.resume#2", strip(p2.call("resume", dialog=d))])
    s1 = snap(c)
    L.append(["snapshot_unchanged_by_resume", s0 == s1])
    L.append(["P2.methods", sorted({x["method"] for x in c.calls(pid=p2.pid)})])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.resume#3", strip(p2.call("resume", dialog=d))])
    L.append(["snapshot", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


def case_F(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    L.append(["P2.invoke_conflict_in_doubt",
              strip(p2.call("invoke", dialog=d, payload="pay-1000", seq=1))])
    L.append(["P2.calls_any", len(c.calls(pid=p2.pid))])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.invoke_conflict_after_commit",
              strip(p2.call("invoke", dialog=d, payload="pay-1000", seq=1))])
    L.append(["P2.invoke_same_after_commit",
              strip(p2.call("invoke", dialog=d, payload="pay-10", seq=1))])
    L.append(["snapshot", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


def case_G(c, L):
    p1, d = crash_p1(c, "pre_b", L)
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.reconcile_async_hold", p2.call("reconcile_async_hold", dialog=d)])
    L.append(["P2.wait_held", p2.call("wait_held")])
    L.append(["P2.reconcile#2", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.retry", strip(p2.call("retry", dialog=d, seq=1))])
    L.append(["P2.release_held(stale answer)", strip(p2.call("release_held"))])
    c.ctl("release", gate="pre_b")
    L.append(["wait_done_invoke_2", c.ctl("wait_done", method="invoke", n=2)])
    L.append(["late_reply_to_P1", late(c, p1)])
    L.append(["snapshot", snap(c)])


def case_H(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    p2.call("recover")
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.reconcile#1", strip(p2.call("reconcile", dialog=d))])
    s = snap(c)
    L.append(["P2.reconcile#2", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.reconcile#3", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.sigkill_rc", p2.sigkill()])
    p3 = c.agent("P3")
    L.append(["P3.recover", strip(p3.call("recover"))])
    L.append(["P3.reconcile", strip(p3.call("reconcile", dialog=d))])
    L.append(["P3.settle", strip(p3.call("settle", dialog=d))])
    L.append(["P3.invoke_same", strip(p3.call("invoke", dialog=d, payload="pay-10", seq=1))])
    L.append(["snapshot_unchanged", snap(c) == s])
    L.append(["P3.calls_any", len(c.calls(pid=p3.pid))])
    L.append(["snapshot", snap(c)])


def case_H2(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.sigkill_rc", p2.sigkill()])
    p3 = c.agent("P3")
    L.append(["P3.recover", strip(p3.call("recover"))])
    L.append(["P3.unresolved", strip(p3.call("unresolved", dialog=d))])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P3.reconcile", strip(p3.call("reconcile", dialog=d))])
    L.append(["snapshot", snap(c)])
    L.append(["P2+P3.invoke_calls", p2_invokes(c, p2) + p2_invokes(c, p3)])


def case_I(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    p2.call("recover")
    c.ctl("store_b_unavailable", on=True)
    L.append(["P2.reconcile(store_b_down)", strip(p2.call("reconcile", dialog=d))])
    c.ctl("store_b_unavailable", on=False)
    c.ctl("set_alive", gw="g1", alive=False)
    L.append(["P2.reconcile(g1_down)", strip(p2.call("reconcile", dialog=d))])
    L.append(["P2.settle(g1_down)", strip(p2.call("settle", dialog=d))])
    L.append(["P2.invoke_same(g1_down)",
              strip(p2.call("invoke", dialog=d, payload="pay-10", seq=1))])
    L.append(["P2.retry(g1_down)", strip(p2.call("retry", dialog=d, seq=1))])
    L.append(["snapshot#1", snap(c)])
    c.ctl("set_alive", gw="g1", alive=True)
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.reconcile", strip(p2.call("reconcile", dialog=d))])
    L.append(["snapshot#2", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


def case_failover(c, L):
    p1, d = crash_p1(c, "tool", L)
    c.ctl("set_alive", gw="g1", alive=False)
    p2 = c.agent("P2")
    p2.call("recover")
    L.append(["P2.resume(g2)", strip(p2.call("resume", gw="g2", dialog=d))])
    L.append(["P2.reconcile(g2)#1", strip(p2.call("reconcile", gw="g2", dialog=d))])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.reconcile(g2)#2", strip(p2.call("reconcile", gw="g2", dialog=d))])
    L.append(["snapshot", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


case_unsupported = case_failover  # same steps; the test asserts different outcomes


def case_R1(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    L.append(["P2.invoke_same_seq1", strip(p2.call("invoke", dialog=d, payload="pay-10", seq=1))])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["snapshot", snap(c)])


def case_R2(c, L):
    p1, d = crash_p1(c, "tool", L)
    p2 = c.agent("P2")
    L.append(["P2.resume", strip(p2.call("resume", dialog=d))])
    L.append(["P2.settle#1", strip(p2.call("settle", dialog=d))])
    L.append(["snapshot#1", snap(c)])
    c.ctl("release", gate="tool")
    L.append(["wait_done_invoke", c.ctl("wait_done", method="invoke", n=1)])
    L.append(["P2.settle#2", strip(p2.call("settle", dialog=d))])
    L.append(["snapshot#2", snap(c)])
    L.append(["P2.invoke_calls", p2_invokes(c, p2)])


CASES = [("A_B", case_AB, ALL), ("C", case_C, ALL), ("D", case_D, ALL), ("D2", case_D2, ALL),
         ("E", case_E, ALL), ("F", case_F, ALL), ("G", case_G, ALL), ("H", case_H, ALL),
         ("H2", case_H2, ALL), ("I", case_I, ALL), ("failover", case_failover, FAILOVER_OK),
         ("unsupported", case_unsupported, ["scoped-endpoint-noticket"]),
         ("R1", case_R1, REGR), ("R2", case_R2, REGR)]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("base")
    p.add_argument("outfile")
    p.add_argument("--repeats", type=int, default=3)
    a = p.parse_args()
    sys.path.insert(0, str(Path(a.repo) / "tests"))
    from restart_harness import Cluster  # noqa: E402  (repo test support code, unmodified)

    base = Path(a.base)
    exc = 0
    with open(a.outfile, "w") as f:
        for r in range(a.repeats):
            for name, fn, modes in CASES:
                for m in modes:
                    wd = base / f"r{r}-{name}-{m}"
                    log: list = []
                    rec = {"case": name, "mode": m, "repeat": r}
                    c = None
                    try:
                        c = Cluster(wd, m)
                        fn(c, log)
                        rec["case_status"] = "returned"
                    except Exception:
                        exc += 1
                        rec["case_status"] = "exception"
                        rec["traceback"] = traceback.format_exc()
                    finally:
                        if c is not None:
                            c.close()
                    rec["steps"] = log
                    rec["stderr_bytes"] = {p_.name: p_.stat().st_size
                                           for p_ in sorted(wd.glob("*.stderr"))} if wd.exists() else {}
                    f.write(json.dumps(rec, sort_keys=True) + "\n")
                    f.flush()
    print(json.dumps({"exceptions": exc, "hash_randomization": sys.flags.hash_randomization}))
    return 1 if exc else 0


if __name__ == "__main__":
    raise SystemExit(main())
