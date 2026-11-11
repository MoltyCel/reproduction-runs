"""Run our checker (vrc.py) over every top-level vector of verdict-record-test-vectors.

Usage: python3 -I run_vectors.py <vectors-checkout> <out.jsonl>

Reads from each vector only the checker's inputs: record_b64, evidence_items,
upper_time_bound, policy and hold. It does not read `expected`, `depends_on_interpretation`
or any other answer. record_sha256 and policy_sha256 are compared with what we compute and
the comparison is recorded.
"""
import base64
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vrc  # noqa: E402

INPUTS = ("record_b64", "evidence_items", "upper_time_bound", "policy", "hold",
          "record_sha256", "policy_sha256", "name")


def main(src, out):
    files = sorted(glob.glob(os.path.join(src, "[a-h][0-9][0-9]-*.json")))
    states = {}
    with open(out, "w", encoding="utf-8") as fh:
        for f in files:
            with open(f, "rb") as vf:
                raw = vf.read()
            v = json.loads(raw)
            v = {k: v[k] for k in INPUTS if k in v}  # nothing else is looked at
            rb = base64.b64decode(v["record_b64"], validate=True)
            rep = vrc.check_case(rb, v["evidence_items"], v["upper_time_bound"],
                                 v["policy"], v.get("hold", []))
            line = {
                "case": v["name"],
                "file": os.path.basename(f),
                "file_sha256": vrc.sha256_hex(raw),
                "record_sha256_matches_vector": vrc.sha256_hex(rb) == v["record_sha256"],
                "policy_sha256_matches_vector": rep.get("policy_sha256") == v["policy_sha256"],
                "summary": vrc.summary_line(rep),
                "report": rep,
            }
            fh.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
            states[rep["state"]] = states.get(rep["state"], 0) + 1
            print("%-48s %s" % (v["name"], line["summary"]))
    print("cases: %d  %s" % (len(files), json.dumps(states, sort_keys=True)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
