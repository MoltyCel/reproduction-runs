"""Compare our per-case reports with the reference checker's, field by field.

Usage: python3 -I compare.py <vectors-checkout> <ours.jsonl> <reference.txt> <out.json>

reference.txt is the output of `vrcheck.py <vector files>` (one line per vector:
path, then the report as JSON). Does not import the reference checker.

Compared per case: the state; each step's result; the step the check names (first
FAIL is not used: -02 Section 4.1 names the last FAILing step, both reports are
recounted the same way from their step results); the inputs named as read from body;
the evidence entries step 2 does not rely on. For each difference the record bytes,
the policy as given and both reports' own wording are recorded. No reading is given.
Also records, separately, where our state or steps differ from the vector's expected
answer.
"""
import base64
import glob
import json
import os
import re
import sys


def entries_ours(rep):
    notes = (rep.get("step_notes") or {}).get("2") or []
    out = []
    for n in notes:
        m = re.match(r"entry (\d+) ", n)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def entries_ref(rep):
    out = []
    for n in rep.get("not_relied_on") or []:
        m = re.match(r"evidence\[(\d+)\]", n)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def named_step(steps):
    if not steps:
        return None
    r = [steps[k] for k in "123"]
    if "FAIL" in r:
        return "FAIL at step %d" % (max(i for i, s in enumerate(r) if s == "FAIL") + 1)
    if "NOT RUN" in r:
        return "NOT RUN at step %d" % (r.index("NOT RUN") + 1)
    return "PASS"


def main(src, ours_path, ref_path, out_path):
    ours = {}
    for ln in open(ours_path, encoding="utf-8"):
        d = json.loads(ln)
        ours[d["file"]] = d["report"]
    ref = {}
    for ln in open(ref_path, encoding="utf-8"):
        if not ln.strip() or ln.startswith("exit="):
            continue
        path, js = ln.split(" ", 1)
        ref[os.path.basename(path)] = json.loads(js)
    files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(src, "[a-h][0-9][0-9]-*.json")))
    rows, diffs, vs_expected, ref_vs_expected = [], [], [], []
    for f in files:
        v = json.load(open(os.path.join(src, f), encoding="utf-8"))
        o, r = ours[f], ref[f]
        fields = {
            "state": (o.get("state"), r.get("state")),
            "step 1": ((o.get("steps") or {}).get("1"), (r.get("steps") or {}).get("1")),
            "step 2": ((o.get("steps") or {}).get("2"), (r.get("steps") or {}).get("2")),
            "step 3": ((o.get("steps") or {}).get("3"), (r.get("steps") or {}).get("3")),
            "named step": (named_step(o.get("steps")), named_step(r.get("steps"))),
            # an absent list and an empty list are compared as equal: neither names an input
            "body_inputs_read": (o.get("body_inputs_read") or [], r.get("body_inputs_read") or []),
            "step 2 entries not relied on": (entries_ours(o) if o.get("steps") else None,
                                             entries_ref(r) if r.get("steps") else None),
        }
        differing = {k: {"ours": a, "reference": b} for k, (a, b) in fields.items() if a != b}
        rows.append({"case": v["name"], "ours": o.get("state"), "reference": r.get("state"),
                     "ours_steps": o.get("steps"), "reference_steps": r.get("steps"),
                     "differs": sorted(differing)})
        if differing:
            diffs.append({
                "case": v["name"],
                "fields": differing,
                "record_sha256": v["record_sha256"],
                "record_bytes": base64.b64decode(v["record_b64"]).decode("utf-8", errors="backslashreplace"),
                "evidence_items_sha256": [__import__("hashlib").sha256(base64.b64decode(i["b64"])).hexdigest()
                                          for i in v["evidence_items"]],
                "policy": v["policy"],
                "hold": v.get("hold", []),
                "ours_wording": {k: o.get(k) for k in ("refused_before_steps", "policy_invalid", "step_notes", "check") if k in o},
                "reference_wording": {k: r.get(k) for k in ("reasons", "not_relied_on", "summary") if k in r},
            })
        e = v["expected"]
        if e.get("state") != r.get("state") or (e.get("steps") is not None and e.get("steps") != r.get("steps")):
            ref_vs_expected.append(v["name"])
        if e.get("state") != o.get("state") or (e.get("steps") is not None and e.get("steps") != o.get("steps")):
            vs_expected.append({"case": v["name"], "expected_state": e.get("state"), "expected_steps": e.get("steps"),
                                "ours_state": o.get("state"), "ours_steps": o.get("steps"),
                                "depends_on_interpretation": v.get("depends_on_interpretation")})
    state_agree = sum(1 for x in rows if x["ours"] == x["reference"])
    steps_agree = sum(1 for x in rows if x["ours_steps"] == x["reference_steps"])
    res = {"cases": len(rows), "state_agrees": state_agree, "steps_agree": steps_agree,
           "cases_with_any_difference": len(diffs), "rows": rows, "differences": diffs,
           "ours_vs_vector_expected": vs_expected,
           "reference_vs_vector_expected": ref_vs_expected}
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    print("cases %d; state agrees %d; all three step results agree %d; cases with any field differing %d"
          % (len(rows), state_agree, steps_agree, len(diffs)))
    for d in diffs:
        print("%-44s %s" % (d["case"], "; ".join("%s ours=%s reference=%s" % (k, json.dumps(x["ours"]), json.dumps(x["reference"]))
                                              for k, x in sorted(d["fields"].items()))))
    print("recount: the reference report differs from the vector's expected answer (state, and steps where given) in %d cases: %s"
          % (len(ref_vs_expected), ", ".join(ref_vs_expected)))
    print("ours differs from the vector's expected answer in %d cases: %s"
          % (len(vs_expected), ", ".join(x["case"] for x in vs_expected)))


if __name__ == "__main__":
    main(*sys.argv[1:5])
