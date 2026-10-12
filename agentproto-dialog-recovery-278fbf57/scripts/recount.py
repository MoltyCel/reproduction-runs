"""Independent recount for agentproto-recovery @ 278fbf5 (v0.2.2).

Does not import agentproto_recovery. Reads the JSONL records written by
driver.py and restart_observe.py, the process-status manifests, the native
CLI outputs, the pytest JUnit XML files, and the committed results/ of the
pinned repo. Compares every recounted value with the printed value in
docs/results.md, docs/experiment_methodology.md and README.md (each claim
carries its file:line). Writes recount/recount.json.

usage: recount.py TAB_DIR
"""
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

CONFIGS = ["global-store", "global-endpoint", "scoped-store", "scoped-endpoint-noticket",
           "scoped-endpoint-ticket", "scoped-endpoint-medticket"]
CONTROL = "scoped-store+UNSAFE_GUESS"
MUST_FAIL = {"revoked", "expired", "terminated", "stale_replay", "wrong_principal"}
VARIANTS = ["noseedA", "noseedB", "seed0"]  # noseedA = reference
REF = "noseedA"
STORE = ["global-store", "scoped-store"]
TICKET = ["scoped-endpoint-ticket", "scoped-endpoint-medticket"]


def load_jsonl(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def b(v):
    return {"True": True, "False": False, "": None}.get(v, v)


def scen_sig(r):
    return (r["code"], r["recovered"], r["correct_association"], r["explicit_failure"],
            json.dumps(r["extra"], sort_keys=True))


def recount_scen(recs):
    out = {"records": len(recs), "exceptions": sum(r["case_status"] != "returned" for r in recs)}
    by_cell = defaultdict(list)
    for r in recs:
        if r["case_status"] == "returned":
            by_cell[r["scenario"]].append(r)
    out["cells"] = len(by_cell)
    out["nondeterministic_cells"] = sorted(s for s, rs in by_cell.items()
                                           if len({scen_sig(x) for x in rs}) != 1)
    first = [rs[0] for rs in by_cell.values()]
    out["incorrect_associations_repeat0"] = sum(x["correct_association"] is False for x in first)
    out["incorrect_associations_any_repeat"] = sum(
        x["correct_association"] is False for rs in by_cell.values() for x in rs)
    out["codes"] = dict(sorted(Counter(x["code"] for x in first).items()))
    out["cell_codes"] = {s: rs[0]["code"] for s, rs in sorted(by_cell.items())}
    out["cell_extra"] = {s: rs[0]["extra"] for s, rs in sorted(by_cell.items())}
    out["cell_correct"] = {s: rs[0]["correct_association"] for s, rs in sorted(by_cell.items())}
    return out


def recount_faults(recs):
    rs = [r for r in recs if r["case_status"] == "returned"]
    legit = [r for r in rs if r["fault"] not in MUST_FAIL]
    viol = [r for r in rs if r["recovered"] and (r["correct_association"] is False
                                                  or r["fault"] in MUST_FAIL)]
    by_fault = {}
    for f in sorted({r["fault"] for r in rs}):
        fr = [r for r in rs if r["fault"] == f]
        by_fault[f] = {"n": len(fr), "codes": dict(sorted(Counter(r["code"] for r in fr).items()))}
    return {
        "records": len(recs), "exceptions": len(recs) - len(rs), "attempts": len(rs),
        "recovered": sum(r["recovered"] for r in rs),
        "explicit_failures": sum(not r["recovered"] for r in rs),
        "incorrect_associations": sum(r["correct_association"] is False for r in rs),
        "safety_violations_recomputed": len(viol),
        "safety_violations_native_flag": sum(bool(r["safety_violation"]) for r in rs),
        "safety_violation_faults": dict(Counter(r["fault"] for r in viol)),
        "recovery_rate_where_permitted": round(sum(r["recovered"] for r in legit) / len(legit), 4)
        if legit else None,
        "by_fault": by_fault,
    }


def fault_row_key(r):
    return (r["mode"], int(r["seed"]), int(r["dialog"]))


def fault_row_sig(r):
    def v(x):
        return b(x) if isinstance(x, str) else x
    return (r["fault"], r["code"], v(r["recovered"]), v(r["correct_association"]),
            v(r["safety_violation"]))


def read_csv(p):
    with p.open(newline="") as f:
        return list(csv.DictReader(f))


def csv_scen(p):
    return {(r["scenario"], r["mode"]): (r["code"], b(r["recovered"]), b(r["correct_association"]),
                                         b(r["explicit_failure"]),
                                         json.dumps(json.loads(r["extra"]), sort_keys=True))
            for r in read_csv(p)}


def diff_maps(a, b_, la, lb):
    out = []
    for k in sorted(set(a) | set(b_), key=str):
        if a.get(k) != b_.get(k):
            out.append({"key": list(k) if isinstance(k, tuple) else k, la: a.get(k), lb: b_.get(k)})
    return out


def junit(p):
    root = ET.parse(p).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root
    cases = []
    for tc in suite.iter("testcase"):
        st = "passed"
        for tag in ("failure", "error", "skipped"):
            if tc.find(tag) is not None:
                st = tag
        cases.append({"file": tc.get("classname", "").split(".")[-1], "name": tc.get("name"),
                      "status": st})
    per_file = defaultdict(Counter)
    for c in cases:
        per_file[c["file"]][c["status"]] += 1
    return {"suite": {k: suite.get(k) for k in ("tests", "failures", "errors", "skipped")},
            "time": suite.get("time"),
            "status": dict(Counter(c["status"] for c in cases)),
            "per_file": {f: dict(v) for f, v in sorted(per_file.items())},
            "names": sorted(f"{c['file']}::{c['name']}" for c in cases)}


def restart_sig(rec):
    """Outcome signature of one observed restart case: every step value
    (identifiers were never recorded)."""
    return json.dumps(rec["steps"], sort_keys=True)


def step(rec, label):
    for k, v in rec["steps"]:
        if k == label:
            return v
    raise KeyError(label)


def main():
    T = Path(sys.argv[1])
    repo = T / "src/repo"
    rep = {"variants": {}, "comparisons": {}, "claims": [], "restart": {}, "pytest": {}}
    case_maps, restart_maps = {}, {}
    for v in VARIANTS:
        R = T / "runs" / v
        status = {(r["config"], r["part"]): r["exit_code"]
                  for r in csv.DictReader((R / "process-status.tsv").open(), delimiter="\t")}
        vr = {"process_status": {f"{k[0]}/{k[1]}": int(x) for k, x in status.items()}}
        scen_all, fault_all = {}, {}
        for c in CONFIGS + [CONTROL]:
            s = load_jsonl(R / f"per-config/{c}.scenarios.jsonl")
            f = load_jsonl(R / f"per-config/{c}.faults.jsonl")
            vr[c] = {"scenarios": recount_scen(s), "faults": recount_faults(f),
                     "stdout_scenarios": (R / f"per-config/{c}.scenarios.stdout").read_text().strip(),
                     "stdout_faults": (R / f"per-config/{c}.faults.stdout").read_text().strip(),
                     "stderr_bytes": (R / f"per-config/{c}.scenarios.stderr").stat().st_size
                     + (R / f"per-config/{c}.faults.stderr").stat().st_size,
                     "sha256_scenarios_jsonl": sha(R / f"per-config/{c}.scenarios.jsonl"),
                     "sha256_faults_jsonl": sha(R / f"per-config/{c}.faults.jsonl")}
            for r in s:
                if r["case_status"] == "returned":
                    scen_all[(r["scenario"], r["mode"], r["repeat"])] = scen_sig(r)
            for r in f:
                if r["case_status"] == "returned":
                    fault_all[fault_row_key(r)] = fault_row_sig(r)
        rep["variants"][v] = vr
        case_maps[v] = (scen_all, fault_all)

        nat = R / "native"
        nat_faults = {fault_row_key(r): fault_row_sig(r) for r in read_csv(nat / "faults/fault_schedule.csv")}
        drv0 = {(k[0], k[1]): sig for k, sig in scen_all.items() if k[2] == 0}
        nat_summary = json.loads((nat / "faults/fault_summary.json").read_text())
        mism = []
        for c in CONFIGS + [CONTROL]:
            m, n = vr[c]["faults"], nat_summary[c]
            for km, kn in [("attempts", "attempts"), ("recovered", "recovered"),
                           ("explicit_failures", "explicit_failures"),
                           ("incorrect_associations", "incorrect_associations"),
                           ("safety_violations_recomputed", "safety_violations"),
                           ("recovery_rate_where_permitted", "recovery_rate_where_recovery_permitted")]:
                if m[km] != n[kn]:
                    mism.append([c, km, m[km], n[kn]])
            for f_, d in n["by_fault"].items():
                mine = m["by_fault"].get(f_, {"n": 0, "codes": {}})
                if mine != {"n": d["n"], "codes": dict(sorted(d["codes"].items()))}:
                    mism.append([c, f"by_fault.{f_}", mine, d])
        comp = {
            "driver_vs_native_fault_rows": diff_maps(fault_all, nat_faults, "driver", "native"),
            "driver_vs_native_scenario_cells": diff_maps(drv0, csv_scen(nat / "scenarios/scenario_matrix.csv"),
                                                         "driver", "native"),
            "recount_vs_native_fault_summary": mism,
        }
        for nf, cf in [("scenarios/scenario_matrix.csv", "scenario_matrix.csv"),
                       ("scenarios/scenario_summary.json", "scenario_summary.json"),
                       ("faults/fault_schedule.csv", "fault_schedule.csv"),
                       ("faults/fault_summary.json", "fault_summary.json"),
                       ("privacy/privacy.json", "privacy.json"),
                       ("privacy/privacy.csv", "privacy.csv")]:
            a, c_ = nat / nf, repo / "results" / cf
            same_bytes = a.read_bytes() == c_.read_bytes()
            same_json = (json.loads(a.read_text()) == json.loads(c_.read_text())) \
                if cf.endswith(".json") else None
            comp[f"native_vs_committed:{cf}"] = {"bytes_equal": same_bytes, "json_equal": same_json}
        rep["comparisons"][v] = comp

        rep["pytest"][v] = junit(nat / "pytest-junit.xml")
        rep["pytest"][v]["summary_line"] = [l for l in (nat / "pytest.stdout").read_text().splitlines()
                                            if " passed" in l or " failed" in l][-1]
        rr = load_jsonl(R / "restart/restart-observe.jsonl")
        restart_maps[v] = rr

    # committed results vs reference driver records
    s0, f0 = case_maps[REF]
    com_f = {fault_row_key(r): fault_row_sig(r) for r in read_csv(repo / "results/fault_schedule.csv")}
    rep["comparisons"]["ref_vs_committed_fault_rows"] = diff_maps(f0, com_f, "ours", "committed")
    rep["comparisons"]["ref_vs_committed_scenario_cells"] = diff_maps(
        {(k[0], k[1]): sig for k, sig in s0.items() if k[2] == 0},
        csv_scen(repo / "results/scenario_matrix.csv"), "ours", "committed")
    rep["comparisons"]["committed_counts"] = {"fault_rows": len(com_f),
                                              "scenario_cells": len(csv_scen(repo / "results/scenario_matrix.csv"))}
    stab = {}
    for v in VARIANTS[1:]:
        s, f = case_maps[v]
        stab[f"{REF}_vs_{v}"] = {
            "scenario_records_differing": diff_maps(s0, s, REF, v),
            "fault_records_differing": diff_maps(f0, f, REF, v),
            "jsonl_sha256_equal": {c: [rep["variants"][REF][c]["sha256_scenarios_jsonl"]
                                       == rep["variants"][v][c]["sha256_scenarios_jsonl"],
                                       rep["variants"][REF][c]["sha256_faults_jsonl"]
                                       == rep["variants"][v][c]["sha256_faults_jsonl"]]
                                   for c in CONFIGS + [CONTROL]},
            "restart_records_differing": [
                [a["case"], a["mode"], a["repeat"]] for a, b_ in zip(restart_maps[REF], restart_maps[v])
                if (a["case"], a["mode"], a["repeat"]) != (b_["case"], b_["mode"], b_["repeat"])
                or restart_sig(a) != restart_sig(b_)],
        }
    rep["comparisons"]["stability"] = stab

    # ---- restart observation: per case x mode, signatures across repeats and variants
    rs = defaultdict(lambda: defaultdict(list))
    for v in VARIANTS:
        for r in restart_maps[v]:
            rs[r["case"]][r["mode"]].append((v, r))
    rsum = {}
    for case, modes in rs.items():
        rsum[case] = {}
        for m, lst in modes.items():
            sigs = Counter(restart_sig(r) for _, r in lst)
            rsum[case][m] = {"runs": len(lst), "exceptions": sum(r["case_status"] != "returned" for _, r in lst),
                             "distinct_outcome_signatures": len(sigs),
                             "stderr_bytes_total": sum(sum(r["stderr_bytes"].values()) for _, r in lst)}
    rep["restart"]["per_case_mode"] = rsum
    ref = {(r["case"], r["mode"], r["repeat"]): r for r in restart_maps[REF]}

    def codes_of(x):
        if isinstance(x, list):
            return [codes_of(y) for y in x]
        if isinstance(x, dict):
            return "/".join(str(x[k]) for k in ("outcome", "code", "status") if k in x and x[k] != "")
        return x
    tab = defaultdict(lambda: defaultdict(Counter))
    for v in VARIANTS:
        for r in restart_maps[v]:
            for k, val in r["steps"]:
                if k.startswith(("P2.", "P3.", "late_reply", "P2+P3")) and k not in (
                        "P2.reconcile_async_hold", "P2.wait_held"):
                    tab[r["case"]][k][json.dumps(codes_of(val))] += 1
    rep["restart"]["step_codes_all_variants"] = {c: {k: dict(v) for k, v in d.items()} for c, d in tab.items()}
    # final execution counts and op-key suffixes
    ex = defaultdict(Counter)
    for v in VARIANTS:
        for r in restart_maps[v]:
            snaps = [val for k, val in r["steps"] if k.startswith("snapshot") and isinstance(val, dict)]
            last = snaps[-1] if snaps else None
            if last:
                ex[r["case"]][json.dumps([last["executions"], last["exec_key_suffix"],
                                          [o["state"] for o in last["a_ops"]],
                                          [o["attempt"] for o in last["a_ops"]],
                                          [o["state"] for o in last["b_ops"]],
                                          [o["attempt"] for o in last["b_ops"]]])] += 1
    rep["restart"]["final_state_counts"] = {c: dict(v) for c, v in ex.items()}

    # gate misses (P1's request did not reach the hold point within the harness bound)
    gm = {}
    extra = T / "runs/extra-noseed"
    all_obs = dict(restart_maps)
    if (extra / "restart/restart-observe.jsonl").exists():
        all_obs["extra-noseed"] = load_jsonl(extra / "restart/restart-observe.jsonl")
    for v, recs in all_obs.items():
        miss = [{"case": r["case"], "mode": r["mode"], "repeat": r["repeat"],
                 "steps_after_miss": [s for s in r["steps"] if not s[0].startswith(("P1.establish",))]}
                for r in recs if [x for k, x in r["steps"] if k.startswith("gate_entered")] != [True]]
        gm[v] = {"case_runs": len(recs), "gate_misses": len(miss), "misses": miss,
                 "exceptions": sum(r["case_status"] != "returned" for r in recs)}
    rep["restart"]["gate_misses"] = gm
    # signatures across ALL observation runs, excluding gate misses
    sig_all = defaultdict(lambda: defaultdict(Counter))
    for v, recs in all_obs.items():
        for r in recs:
            if [x for k, x in r["steps"] if k.startswith("gate_entered")] == [True]:
                sig_all[r["case"]][r["mode"]][restart_sig(r)] += 1
    rep["restart"]["distinct_signatures_excluding_gate_misses"] = {
        c: {m: {"runs": sum(cnt.values()), "distinct": len(cnt)} for m, cnt in d.items()}
        for c, d in sig_all.items()}
    pr = []
    for p in sorted((extra / "pytest-restart").glob("junit-*.xml")) if extra.exists() else []:
        j = junit(p)
        pr.append({"file": p.name, "status": j["status"],
                   "failed": [n for n, s in zip(j["names"], [None] * len(j["names"]))][:0]})
        root = ET.parse(p).getroot()
        suite = root.find("testsuite") if root.tag == "testsuites" else root
        pr[-1]["failed"] = [f"{tc.get('classname').split('.')[-1]}::{tc.get('name')}"
                            for tc in suite.iter("testcase") if tc.find("failure") is not None
                            or tc.find("error") is not None]
    rep["pytest"]["extra-noseed-restart-files"] = pr

    # ---- claims: printed value vs recounted value
    V = rep["variants"][REF]
    P = rep["pytest"][REF]
    claims = rep["claims"]

    def claim(src, what, printed, ours, match=None):
        claims.append({"source": src, "what": what, "printed": printed, "ours": ours,
                       "match": (printed == ours) if match is None else match})

    E2 = {"global-store": (70, 200, 0, 0, 0.620, "results.md:307"),
          "global-endpoint": (113, 157, 0, 0, 1.000, "results.md:308"),
          "scoped-store": (70, 200, 0, 0, 0.620, "results.md:309"),
          "scoped-endpoint-noticket": (0, 270, 0, 0, 0.000, "results.md:310"),
          "scoped-endpoint-ticket": (67, 203, 0, 0, 0.593, "results.md:311"),
          "scoped-endpoint-medticket": (67, 203, 0, 0, 0.593, "results.md:312"),
          CONTROL: (78, 192, 13, 13, 0.690, "results.md:313")}
    for c, (rec, exf, inc, sv, rate, src) in E2.items():
        m = V[c]["faults"]
        for name, pv, ov in [("recovered", rec, m["recovered"]),
                             ("explicit failures", exf, m["explicit_failures"]),
                             ("incorrect assoc.", inc, m["incorrect_associations"]),
                             ("safety violations", sv, m["safety_violations_recomputed"]),
                             ("rate where permitted (3 dp)", rate, round(m["recovery_rate_where_permitted"], 3))]:
            claim(f"docs/{src}", f"E2 {c}: {name}", pv, ov)
    claim("docs/results.md:301", "attempts per mode (3 seeds x 90)", 270,
          sorted({V[c]["faults"]["attempts"] for c in CONFIGS + [CONTROL]}) == [270] and 270)
    ft = {c: V[c]["faults"]["by_fault"].get("foreign_ticket") for c in CONFIGS}
    claim("docs/results.md:315", "foreign_ticket attempts per mode", 24, sorted({x["n"] for x in ft.values()}) == [24] and 24)
    claim("docs/results.md:315-316", "foreign_ticket store + global-endpoint: 24 OK",
          {"OK": 24}, [ft[c]["codes"] for c in STORE + ["global-endpoint"]],
          all(ft[c]["codes"] == {"OK": 24} for c in STORE + ["global-endpoint"]))
    claim("docs/results.md:316-317", "foreign_ticket ticket modes: 21 TICKET_MISMATCH, 3 MAPPING_NOT_FOUND",
          {"TICKET_MISMATCH": 21, "MAPPING_NOT_FOUND": 3}, [ft[c]["codes"] for c in TICKET],
          all(ft[c]["codes"] == {"MAPPING_NOT_FOUND": 3, "TICKET_MISMATCH": 21} for c in TICKET))
    tot = sum(V[c]["faults"]["attempts"] for c in CONFIGS)
    wrong = sum(V[c]["faults"]["incorrect_associations"] for c in CONFIGS)
    mf_ok = sum(1 for c in CONFIGS for f_, d in V[c]["faults"]["by_fault"].items()
                if f_ in MUST_FAIL for code, n in d["codes"].items() if code == "OK")
    claim("docs/results.md:321-323 / README.md:40-43", "1,620 attempts in six modes, 0 wrong dialog, 0 MUST_FAIL resumed",
          [1620, 0, 0], [tot, wrong, mf_ok])
    claim("README.md:35-36", "scoped-endpoint-noticket recovered 0 of 270", [0, 270],
          [V["scoped-endpoint-noticket"]["faults"]["recovered"], V["scoped-endpoint-noticket"]["faults"]["attempts"]])
    claim("README.md:42-43", "negative control wrong 13 of 270", [13, 270],
          [V[CONTROL]["faults"]["safety_violations_recomputed"], V[CONTROL]["faults"]["attempts"]])
    claim("docs/experiment_methodology.md:26-27", "negative control errors in fault schedule", 23,
          V[CONTROL]["faults"]["incorrect_associations"])
    claim("docs/experiment_methodology.md:27", "negative control T06: OK, wrong association",
          ["OK", False], [V[CONTROL]["scenarios"]["cell_codes"].get("T06"),
                          V[CONTROL]["scenarios"]["cell_correct"].get("T06")])
    # E1
    cells = sum(V[c]["scenarios"]["cells"] for c in CONFIGS + [CONTROL])
    claim("docs/results.md:283 / results.md:20", "E1 cells (25 x 6 + 2)", 152, cells)
    claim("docs/results.md:283", "repeats per cell", 3,
          sorted({V[c]["scenarios"]["records"] // V[c]["scenarios"]["cells"] for c in CONFIGS + [CONTROL]}) == [3] and 3)
    nd = sum(len(V[c]["scenarios"]["nondeterministic_cells"]) for c in CONFIGS + [CONTROL])
    claim("docs/results.md:285", "cells with differing repeats", 0, nd)
    claim("docs/results.md:286", "incorrect associations outside control", 0,
          sum(V[c]["scenarios"]["incorrect_associations_any_repeat"] for c in CONFIGS))
    claim("docs/results.md:286-287", "incorrect associations control (T06, per cell)", 1,
          V[CONTROL]["scenarios"]["incorrect_associations_repeat0"])
    t21 = {c: (V[c]["scenarios"]["cell_codes"]["T21"], V[c]["scenarios"]["cell_correct"]["T21"]) for c in CONFIGS}
    claim("docs/results.md:288-290", "T21: TICKET_MISMATCH in ticket modes; OK+correct in store/global-endpoint; noticket fails",
          "as printed", t21,
          all(t21[c][0] == "TICKET_MISMATCH" for c in TICKET)
          and all(t21[c] == ("OK", True) for c in STORE + ["global-endpoint"])
          and t21["scoped-endpoint-noticket"][0] != "OK")
    t22 = {c: (V[c]["scenarios"]["cell_codes"]["T22"], V[c]["scenarios"]["cell_extra"]["T22"]) for c in CONFIGS}
    claim("docs/results.md:291-294", "T22 per mode (code, extra)", "IN_PROGRESS, NOT_EXECUTED, OPERATION_ABORTED, retry OK, 1 execution, every mode",
          t22, len({json.dumps(x, sort_keys=True) for x in t22.values()}) == 1)
    t23 = {c: (V[c]["scenarios"]["cell_codes"]["T23"], V[c]["scenarios"]["cell_extra"]["T23"]) for c in CONFIGS}
    claim("docs/results.md:295-296", "T23 per mode (code, extra)", "SEQUENCE_CONFLICT every mode, 1 execution, retry deduplicated",
          t23, len({json.dumps(x, sort_keys=True) for x in t23.values()}) == 1)
    claim("docs/results.md:20-22", "re-run: 1,890 fault rows identical to committed", 1890,
          (len(f0) == 1890 and not rep["comparisons"]["ref_vs_committed_fault_rows"]) and 1890)
    # E3 privacy: values read from the native privacy.json of this run (his analysis code)
    pj = json.loads((T / "runs" / REF / "native/privacy/privacy.json").read_text())
    E3 = {"global-store": ("3 of 3", 1.0, None, 1, {"GW1": 1.0}, 1.0, 333),
          "global-endpoint": ("4 of 4", 1.0, 1.0, 1, {"GW1": 1.0, "GW2": 1.0}, 1.0, 334),
          "scoped-store": ("2 of 3", 0.0, None, 0, {"GW1": 1.0}, 1.0, 335),
          "scoped-endpoint-noticket": ("3 of 4", 0.0, 1.0, 0, {"GW1": 1.0, "GW2": 0.0}, 1.0, 336),
          "scoped-endpoint-ticket": ("4 of 4", 1.0, 1.0, 2, {"GW1": 1.0, "GW2": 1.0}, 1.0, 337),
          "scoped-endpoint-medticket": ("3 of 4", 0.0, 1.0, 0, {"GW1": 1.0, "GW2": 1.0}, 1.0, 338)}
    for c, (dom, ab, gg, dist, link, order, line) in E3.items():
        x = pj[c]
        jp = x["identifier_join_fraction_by_domain_pair"]
        ours = (f"{x['max_domains_sharing_one_value']} of {len(x['domains'])}", jp["A~B"],
                jp.get("GW1~GW2"), x["mean_distinct_A_B_shared_values_per_dialog"],
                x["gateway_can_link_upstream_downstream"],
                x["order_based_A_B_join_accuracy_sequential_workload"])
        claim(f"docs/results.md:{line}", f"E3 {c} (6 values, from native privacy.json)",
              [dom, ab, gg, dist, link, order], list(ours))
    claim("docs/results.md:328 / methodology.md:69", "E3 dialogs per mode", 50,
          sorted({pj[c]["dialogs"] for c in CONFIGS}) == [50] and 50)
    # pytest
    pf = P["per_file"]
    claim("README.md:83-84,187 / results.md:246,252", "pytest total passed", 379, P["status"].get("passed"))
    claim("results.md:246", "failures/errors/skips", 0,
          P["status"].get("failure", 0) + P["status"].get("error", 0) + P["status"].get("skipped", 0))
    claim("results.md:60-61,255 / README.md:83", "test_process_restart.py passed", 66, pf["test_process_restart"].get("passed"))
    claim("results.md:60,255", "test_process_restart_regression.py passed", 8, pf["test_process_restart_regression"].get("passed"))
    claim("results.md:61-62 / README.md:218", "restart regression + acceptance together", 74,
          pf["test_process_restart"].get("passed", 0) + pf["test_process_restart_regression"].get("passed", 0))
    claim("README.md:187", "tests that start real OS processes (restart files)", 74,
          sum(sum(pf[f].values()) for f in ("test_process_restart", "test_process_restart_regression")))
    claim("results.md:108,247-248,255 / README.md:220", "test_review_v022.py passed", 72, pf["test_review_v022"].get("passed"))
    claim("README.md:77", "new audit test cases", 72, sum(pf["test_review_v022"].values()))
    older = sum(sum(c.values()) for f, c in pf.items()
                if f not in ("test_process_restart", "test_process_restart_regression", "test_review_v022"))
    claim("results.md:247", "tests from v0.2.1 (other files)", 233, older)
    claim("results.md:195 / README.md:105", "test_operation_ledger_integrity.py passed", 44,
          pf["test_operation_ledger_integrity"].get("passed"))
    names = P["names"]
    for prefix, n, line in [("test_review_v022::test_2a_", 12, "132"), ("test_review_v022::test_2b_", 12, "132")]:
        claim(f"results.md:{line}", f"{prefix} cases (2a+2b = 24)", n, sum(1 for x in names if x.startswith(prefix)))
    rows = [("test_a_b_", 6, "66"), ("test_c_", 6, "67"), ("test_d_not_", 6, "68"), ("test_d2_", 6, "69"),
            ("test_e_", 6, "70"), ("test_f_", 6, "71"), ("test_g_", 6, "72"), ("test_h_repeated", 6, "73"),
            ("test_h2_", 6, "74"), ("test_i_", 6, "75"), ("test_restart_combined_with_gateway_failover", 5, "76"),
            ("test_restart_combined_with_failover_unsupported", 1, "77")]
    for prefix, n, line in rows:
        claim(f"docs/results.md:{line}", f"test_process_restart.py {prefix}* parametrised cases",
              n, sum(1 for x in names if x.startswith("test_process_restart::" + prefix)))
    # baseline v0.2.1 (regression file of this revision against the v0.2.1 package)
    bj = T / "runs/baseline-v021/pytest-junit.xml"
    if bj.exists():
        bl = junit(bj)
        rep["pytest"]["baseline-v021"] = bl
        claim("results.md:53 / README.md:60-61", "regression tests on unmodified v0.2.1: failed", 8,
              bl["status"].get("failure"))
    # restart table, behaviour (reference variant, all repeats)
    def all_rec(case):
        return [r for r in restart_maps[REF] if r["case"] == case]
    def chk(case, pred):
        rs_ = all_rec(case)
        return sum(1 for r in rs_ if pred(r)), len(rs_)
    def outc(v):
        return [(x.get("outcome"), x.get("code"), x.get("status")) for x in v]
    checks = [
        ("docs/results.md:66", "A,B: SIGKILL -9, row SENT->IN_DOUBT, B PENDING, 0 executions, P2 sent nothing",
         "A_B", lambda r: step(r, "P1.sigkill_rc") == -9 and step(r, "snapshot")["a_ops"][0]["state"] == "IN_DOUBT"
         and step(r, "snapshot")["b_ops"][0]["state"] == "PENDING" and step(r, "snapshot")["executions"] == 0
         and step(r, "P2.invoke_calls") == 0 and step(r, "snapshot")["a_next_seq"] == [2]),
        ("docs/results.md:67", "C: UNRESOLVED/IN_PROGRESS, late OK to nobody, COMMITTED done:pay-10, attempt 1, 1 exec key :1:1",
         "C", lambda r: outc(step(r, "P2.reconcile#1")) == [("UNRESOLVED", "OUTCOME_UNKNOWN", "IN_PROGRESS")]
         and step(r, "late_reply_to_P1")[0]["code"] == "OK"
         and step(r, "P2.reconcile#2")[0]["outcome"] == "COMMITTED"
         and step(r, "snapshot#2")["a_ops"][0]["attempt"] == 1 and step(r, "snapshot#2")["exec_key_suffix"] == ["1:1"]
         and step(r, "P2.invoke_calls") == 0),
        ("docs/results.md:68", "D: NOT_EXECUTED, fence 1, late OPERATION_ABORTED, 0 exec, retry COMMITTED attempt 2, 1 exec, next_seq 2",
         "D", lambda r: step(r, "P2.reconcile")[0]["outcome"] == "NOT_EXECUTED"
         and step(r, "snapshot#1")["b_fences"] == [1] and step(r, "late_reply_to_P1")[0]["code"] == "OPERATION_ABORTED"
         and step(r, "snapshot#2")["executions"] == 0 and step(r, "P2.retry")["status"] == "COMMITTED"
         and step(r, "snapshot#3")["a_ops"][0]["attempt"] == 2 and step(r, "snapshot#3")["executions"] == 1
         and step(r, "snapshot#3")["a_next_seq"] == [2]),
        ("docs/results.md:69", "D2: NOT_EXECUTED (fenced at tool), old executor refused, retry once under key :1:2",
         "D2", lambda r: step(r, "P2.reconcile")[0]["outcome"] == "NOT_EXECUTED"
         and step(r, "late_reply_to_P1")[0]["code"] == "OPERATION_ABORTED"
         and step(r, "snapshot#2")["exec_key_suffix"] == ["1:2"]),
        ("docs/results.md:70", "E: resume x2 changes nothing, only resume calls, same after resolution",
         "E", lambda r: step(r, "snapshot_unchanged_by_resume") is True and step(r, "P2.methods") == ["resume"]
         and step(r, "snapshot")["executions"] == 1 and step(r, "P2.invoke_calls") == 0),
        ("docs/results.md:71", "F: SEQUENCE_CONFLICT in doubt and after commit, no call; same payload deduplicated",
         "F", lambda r: step(r, "P2.invoke_conflict_in_doubt")["code"] == "SEQUENCE_CONFLICT"
         and step(r, "P2.calls_any") == 0 and step(r, "P2.invoke_conflict_after_commit")["code"] == "SEQUENCE_CONFLICT"
         and step(r, "P2.invoke_same_after_commit")["detail"] == "deduplicated"),
        ("docs/results.md:72", "G: stale NOT_EXECUTED applied:false, late original OK deduplicated, 1 exec",
         "G", lambda r: step(r, "P2.release_held(stale answer)")[0]["applied"] is False
         and step(r, "late_reply_to_P1")[0]["detail"] == "deduplicated" and step(r, "snapshot")["executions"] == 1),
        ("docs/results.md:73", "H: further reconciles and P3 change nothing, P3 sends nothing",
         "H", lambda r: step(r, "snapshot_unchanged") is True and step(r, "P3.calls_any") == 0),
        ("docs/results.md:74", "H2: P3 finds IN_DOUBT, resolves COMMITTED, 1 exec",
         "H2", lambda r: step(r, "P3.unresolved")[0]["state"] == "IN_DOUBT"
         and step(r, "P3.reconcile")[0]["outcome"] == "COMMITTED" and step(r, "snapshot")["executions"] == 1),
        ("docs/results.md:75", "I: DOWNSTREAM_UNAVAILABLE, GATEWAY_DOWN, local refusal, INVALID_STATE, 0 exec, then COMMITTED",
         "I", lambda r: step(r, "P2.reconcile(store_b_down)")[0]["code"] == "DOWNSTREAM_UNAVAILABLE"
         and step(r, "P2.reconcile(g1_down)")[0]["code"] == "GATEWAY_DOWN"
         and step(r, "P2.invoke_same(g1_down)")["status"] == "IN_DOUBT"
         and step(r, "P2.retry(g1_down)")["code"] == "INVALID_STATE"
         and step(r, "snapshot#1")["executions"] == 0 and step(r, "P2.reconcile")[0]["outcome"] == "COMMITTED"),
        ("docs/results.md:76", "restart + failover: UNRESOLVED then COMMITTED via G2, 1 exec",
         "failover", lambda r: step(r, "P2.reconcile(g2)#1")[0]["outcome"] == "UNRESOLVED"
         and step(r, "P2.reconcile(g2)#2")[0]["outcome"] == "COMMITTED" and step(r, "snapshot")["executions"] == 1),
        ("docs/results.md:77", "unsupported: MAPPING_NOT_FOUND, reconcile UNRESOLVED, IN_DOUBT, 1 exec, nothing resent",
         "unsupported", lambda r: step(r, "P2.resume(g2)")["code"] == "MAPPING_NOT_FOUND"
         and step(r, "P2.reconcile(g2)#2")[0]["code"] == "MAPPING_NOT_FOUND"
         and step(r, "snapshot")["a_ops"][0]["state"] == "IN_DOUBT" and step(r, "snapshot")["executions"] == 1
         and step(r, "P2.invoke_calls") == 0),
    ]
    for src, what, case, pred in checks:
        ok, n = chk(case, pred)
        claim(src, f"restart {what} [observed runs {REF}]", f"{n}/{n}", f"{ok}/{n}")

    for c in claims:
        c["match"] = bool(c["match"])
    rep["claims_summary"] = {"total": len(claims), "match": sum(c["match"] for c in claims),
                             "mismatch": [c for c in claims if not c["match"]]}
    out = T / "recount" / "recount.json"
    out.write_text(json.dumps(rep, indent=1, sort_keys=True, default=list) + "\n")
    print(json.dumps({v: {k: (len(x) if isinstance(x, list) else x) for k, x in rep["comparisons"][v].items()}
                      for v in VARIANTS}, indent=1))
    for k in ["ref_vs_committed_fault_rows", "ref_vs_committed_scenario_cells"]:
        print(k, len(rep["comparisons"][k]))
    for k, x in stab.items():
        print(k, {a: (len(b_) if isinstance(b_, list) else all(all(p) for p in b_.values()))
                  for a, b_ in x.items()})
    print("claims:", len(claims), "mismatch:", [(c["source"], c["what"], c["printed"], c["ours"])
                                                for c in rep["claims_summary"]["mismatch"]])


if __name__ == "__main__":
    main()
