#!/usr/bin/env python3
"""Independent reader for giskard09/argentum-core settlement-evidence-ref-v1.

Built from docs/spec/settlement-evidence-ref.md and the comparator_rule in vectors.json
at 225a617d. It does not import or read the project's verify.py or jcs.py.

Usage: python3 -I gk_reader.py <vectors.json> <inline-artifact.json>
"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jcs import jcs_bytes  # our own RFC 8785 implementation

EXPECTED_INLINE = "f909081a79e81d6f5b3f914cf74c96cb51c764722bad012278d70b31f582c8a1"
REQUIRED = ("network", "transaction", "payer_debit", "payee_credit", "version")


def side_ok(s):
    return isinstance(s, dict) and all(isinstance(s.get(k), str) and s.get(k) for k in ("address", "amount", "asset"))


def derive_checks(art, offer, declared):
    """Recompute what the bytes allow. ledger_recomputed is a declaration the spec keeps
    in the vector (external resolution, not performed); it is taken as declared, and we
    check only that a 'true' declaration is not contradicted by missing values."""
    d, c = art.get("payer_debit"), art.get("payee_credit")
    lr = bool(declared.get("ledger_recomputed")) and side_ok(d) and side_ok(c)
    paired = side_ok(d) and side_ok(c) and d["amount"] == c["amount"] and d["asset"] == c["asset"]
    if art.get("offer_identity_ref") and offer is not None:
        mo = paired and d["amount"] == offer.get("maxAmountRequired") and d["asset"] == offer.get("asset") \
            and c["address"] == offer.get("payTo")
    else:
        mo = True  # comparator_rule: matches_offer applies only when an offer is present and supplied
    tp = isinstance(art.get("transaction"), str) and art["transaction"] != ""
    return {"ledger_recomputed": lr, "debit_credit_paired": paired, "matches_offer": mo, "transaction_present": tp}


def main(vec_path, inline_path):
    doc = json.load(open(vec_path, encoding="utf-8"))
    bad = 0
    pos_ok = False
    print("== vectors (our reader)")
    for v in doc["vectors"]:
        art = v["settlement_artifact"]
        digest = hashlib.sha256(jcs_bytes(art)).hexdigest()
        dig_ok = digest == v["settlement_evidence_ref"]
        missing = [k for k in REQUIRED if k not in art]
        checks = derive_checks(art, v.get("referenced_offer"), v.get("checks", {}))
        verdict = "PASS" if (dig_ok and not missing and all(checks.values())) else "FAIL"
        checks_agree = checks == v.get("checks")
        agree = verdict == v["expected"] and checks_agree
        bad += not agree
        if v["id"] == "settlement-matched-001":
            pos_ok = verdict == "PASS"
        failing = [k for k, x in checks.items() if not x]
        print(f"{'agree   ' if agree else 'DISAGREE'} {v['id']:40} expected={v['expected']} got={verdict} "
              f"digest={'match' if dig_ok else 'MISMATCH'} checks={'same' if checks_agree else 'DIFF'} failing={failing or '-'}")
    n = len(doc["vectors"])
    print(f"{n - bad}/{n} agree on verdict and all four checks")
    print(f"positive control settlement-matched-001: {'PASSED' if pos_ok else 'FAILED - run does not count'}")

    print("== inline artifact (comment 6202120269)")
    art = json.load(open(inline_path, encoding="utf-8"))
    digest = hashlib.sha256(jcs_bytes(art)).hexdigest()
    print(f"settlement_evidence_ref = {digest}")
    print(f"expected                = {EXPECTED_INLINE}  -> {'match' if digest == EXPECTED_INLINE else 'MISMATCH'}")
    same_as = [v["id"] for v in doc["vectors"] if v["settlement_artifact"] == art]
    print(f"same artifact as vector: {same_as or '-'}")
    print(f"transaction_present: {isinstance(art.get('transaction'), str) and art['transaction'] != ''}")

    print("== canonicalizer control (RFC 8785 section 3.2.3 sorting example)")
    keys = ["€", "\r", "דּ", "1", "\U0001F600", "\u0080", "ö"]
    obj = {k: i for i, k in enumerate(keys)}
    ours = [k for k in json.loads(jcs_bytes(obj).decode())]
    rfc = ["\r", "1", "\u0080", "ö", "€", "\U0001F600", "דּ"]
    cp = sorted(keys)
    print(f"our order matches RFC 8785 example: {ours == rfc}; code-point order would match: {cp == rfc}")
    ok = bad == 0 and pos_ok and digest == EXPECTED_INLINE and ours == rfc
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
