"""Per-configuration driver for agentproto-recovery @ 278fbf5 (v0.2.2).

Runs one configuration (mode) in one process and writes one JSONL record per
case. Uses only the package's public evaluation entry points
(run_scenario, cli._fault_run); no repo code is modified or patched.

usage: driver.py MODE PART OUTFILE [--unsafe] [--repeats N] [--n N] [--seeds S ...]
  PART = scenarios | faults
"""
import argparse
import json
import sys
import traceback

from agentproto_recovery import cli
from agentproto_recovery.evaluation import SCENARIOS, run_scenario


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("mode")
    p.add_argument("part", choices=["scenarios", "faults"])
    p.add_argument("outfile")
    p.add_argument("--unsafe", action="store_true")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--n", type=int, default=90)
    p.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    p.add_argument("--only", nargs="+", default=None, help="scenario subset")
    a = p.parse_args()
    exc_count = 0
    with open(a.outfile, "w") as f:
        if a.part == "scenarios":
            names = a.only or list(SCENARIOS)
            for s in names:
                for r in range(a.repeats):
                    rec = {"part": "scenarios", "scenario": s, "mode_arg": a.mode,
                           "unsafe": a.unsafe, "repeat": r}
                    try:
                        o = run_scenario(s, a.mode, unsafe_guess=a.unsafe)
                        rec.update(case_status="returned", mode=o.mode, code=o.code,
                                   recovered=o.recovered,
                                   correct_association=o.correct_association,
                                   explicit_failure=o.explicit_failure, extra=o.extra)
                    except Exception:
                        exc_count += 1
                        rec.update(case_status="exception", traceback=traceback.format_exc())
                    f.write(json.dumps(rec, sort_keys=True) + "\n")
        else:
            for seed in a.seeds:
                try:
                    rows = cli._fault_run(a.mode, a.n, seed, a.unsafe)
                    for row in rows:
                        row = dict(row, part="faults", case_status="returned", mode_arg=a.mode)
                        f.write(json.dumps(row, sort_keys=True) + "\n")
                except Exception:
                    exc_count += 1
                    f.write(json.dumps({"part": "faults", "mode_arg": a.mode, "seed": seed,
                                        "case_status": "exception",
                                        "traceback": traceback.format_exc()}) + "\n")
    print(json.dumps({"mode": a.mode, "part": a.part, "unsafe": a.unsafe,
                      "exceptions": exc_count, "hash_randomization": sys.flags.hash_randomization}))
    return 1 if exc_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
