"""Recompute -02 Appendix A.2 from the published draft text, and check the record.

Usage: python3 -I a2_from_text.py <draft-wright-verdict-record-02.txt>

Takes the parent hop, the child hop and the verdict record from the text of Appendix A.2
(RFC 8792 single-backslash folding undone, page breaks removed), forms the record's
canonical bytes (Section 2.1), and compares the three digests with the values the draft
states. Then checks the record under a policy of our own that reads inputs from evidence
only, with each of our two readings of the hop format. Uses nothing from the vectors.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vrc  # noqa: E402

STATED = {
    "record": "62017940a8ddddd5ddd7ff46c8ff2a6ce79dfcccb775d767b8dff8db0ebe19ed",
    "parent": "1336337e88adc67853b80b4998363210dc5c0797cc7b7c722128cecc56a38c14",
    "child": "8886795d4403b5cd8820eb813ee0724f1d6d5d383124364b09cdc5020639e00c",
}
POLICY = {
    "judgement_kinds": [],
    "formats": [vrc.FMT_HOP],
    "max_depth": 0,
    "inputs_from_evidence_only": True,
}
# Section 3: the checker establishes the upper time bound itself. No container is in this
# run, so the bound is a fixed input of ours: the date of the draft.
UPPER = "2026-11-02T00:00:00.000000Z"


def appendix(text):
    a = text.index("A.2.  A Rule Re-run on Cited Delegation Records\n", text.index("Appendix A.  Examples"))
    b = text.index("Appendix B.  Open Questions", a)
    lines = []
    for ln in text[a:b].split("\n"):
        if ln.startswith("\f") or re.match(r"Wright\s+Expires", ln) or re.match(r"Internet-Draft\s+Verdict Records", ln):
            continue
        lines.append(ln)
    return lines


def blocks(lines):
    """Each artwork block after a folding NOTE line, unfolded per RFC 8792 Section 7.2."""
    out, i = [], 0
    while i < len(lines):
        if "NOTE: '\\' line wrapping per RFC 8792" in lines[i]:
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            body = []
            while i < len(lines):
                ln = lines[i]
                if ln.strip() == "":
                    # a blank line ends the block unless the JSON object is still open
                    joined = "\n".join(body)
                    if joined.count("{") == joined.count("}") and body:
                        break
                    i += 1
                    continue
                if not ln.startswith("   "):
                    break
                body.append(ln[3:])
                i += 1
            s = "\n".join(body)
            s = re.sub(r"\\\n[ ]*", "", s)  # undo single-backslash folding
            out.append(s)
        i += 1
    return out


def main(path):
    text = open(path, encoding="utf-8").read()
    bl = blocks(appendix(text))
    if len(bl) != 3:
        sys.exit("expected three artwork blocks in A.2, found %d" % len(bl))
    parent_b, child_b = bl[0].encode(), bl[1].encode()
    record_obj = json.loads(bl[2])
    record_b = vrc.canonical(record_obj)
    got = {"parent": vrc.sha256_hex(parent_b), "child": vrc.sha256_hex(child_b),
           "record": vrc.sha256_hex(record_b)}
    print("draft_sha256:", vrc.sha256_hex(open(path, "rb").read()))
    for k in ("record", "parent", "child"):
        print("%-7s computed %s stated %s equal %s" % (k, got[k], STATED[k], got[k] == STATED[k]))
    print("parent hop bytes:", parent_b.decode())
    print("child hop bytes: ", child_b.decode())
    print("record canonical bytes:", record_b.decode())
    print("parent hop already canonical:", vrc.canonical(json.loads(parent_b)) == parent_b)
    print("child hop already canonical: ", vrc.canonical(json.loads(child_b)) == child_b)
    print("policy:", vrc.canonical(POLICY).decode())
    print("policy_sha256:", vrc.sha256_hex(vrc.canonical(POLICY)))
    print("upper_time_bound (our input):", UPPER)
    import base64
    items = [{"b64": base64.b64encode(parent_b).decode()}, {"b64": base64.b64encode(child_b).decode()}]
    runs = [
        ("hop format requires a signature (expected by the job: held at step 2)",
         ["appendix_a2_rule.py", "appendix_a2_hops_signature_required.py"]),
        ("hop format read without a signature (parse only)",
         ["appendix_a2_rule.py", "appendix_a2_hops_parse_only.py"]),
    ]
    for label, hold in runs:
        rep = vrc.check_case(record_b, items, UPPER, POLICY, hold)
        print("--", label)
        print("   ", vrc.summary_line(rep), "|", rep.get("check"))
        print("   ", json.dumps(rep, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
