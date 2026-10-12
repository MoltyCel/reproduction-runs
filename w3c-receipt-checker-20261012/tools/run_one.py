"""Run the pinned receipt checker on one corpus copy and record the result.

    env/bin/python -I tools/run_one.py <run-dir> <label> <out.json> <hash-seed>

<run-dir> holds `checkers/` and `vectors/v1.4.0-conformance/` as extracted from
ccs-conformance-vectors at effff90f231d11bb3be93d3d0d0792f36934cc78 (A unchanged, B/C
manipulated copies).

Two independent views of the same run:
  1. native process: the checker is started exactly as in message 0051
     (`python checkers/independent_checker.py vectors/v1.4.0-conformance`, cwd = run-dir);
     stdout, stderr, exit code and the printed footer are kept verbatim.
  2. per-case records: the checker module is loaded from the same file, and its own
     verify_manifest / find_case_dirs / verify_case are called. Native verdict and reason
     are taken from those objects; the recount is done here from these records, never from
     the footer.
The per-case status lines in stdout are parsed and compared with the records.

The checker prints Python sets via repr (10c, `trace_ids differ: {...}`), so its stdout
depends on string hash randomisation. Both views therefore run under the same fixed
PYTHONHASHSEED, which is recorded; the records part runs in a child process for that.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import os
import subprocess
import sys

import jcs

CORPUS = "vectors/v1.4.0-conformance"
CHECKER = "checkers/independent_checker.py"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def input_digest(corpus: pathlib.Path) -> tuple[str, dict]:
    """SHA-256 over JCS({relative path: sha256(file bytes)}) for every regular file."""
    files = {p.relative_to(corpus).as_posix(): sha(p.read_bytes())
             for p in sorted(corpus.rglob("*")) if p.is_file()}
    return sha(jcs.canonicalize(files)), files


def main() -> int:
    run, label, out = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    seed = sys.argv[4]
    if os.environ.get("PYTHONHASHSEED") != seed or not sys.flags.ignore_environment == 0:
        env = {"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": seed}
        return subprocess.run([sys.executable, "-s", "-P", os.path.abspath(__file__),
                               *sys.argv[1:]], env=env).returncode
    corpus = run / CORPUS

    proc = subprocess.run([sys.executable, CHECKER, CORPUS], cwd=run, capture_output=True,
                          env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": seed})
    stdout = proc.stdout.decode("utf-8")
    footer = [l for l in stdout.splitlines() if l.startswith(("Checks:", "Cases:"))]
    printed_status = dict(
        (m.group(2), m.group(1)) for m in re.finditer(r"^(✓ PASS|✗ FAIL)  (.+)$", stdout, re.M))

    spec = importlib.util.spec_from_file_location("independent_checker", run / CHECKER)
    chk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chk)

    manifest_ok, manifest_errors = chk.verify_manifest(corpus)
    manifest = json.loads((corpus / "manifest.json").read_bytes())
    listed = set(manifest.get("files", {}))
    case_dirs = chk.find_case_dirs(corpus) if manifest_ok else []

    records, n_checks, n_false = [], 0, 0
    for cd in case_dirs:
        cid = cd.relative_to(corpus).as_posix()
        res = chk.verify_case(cd)
        checks = [c for rr in res["receipts"] for c in rr["checks"]]
        n_checks += len(checks)
        n_false += sum(1 for c in checks if c[1] is False)
        case_files = [p.relative_to(corpus).as_posix() for p in sorted(cd.rglob("*")) if p.is_file()]
        records.append({
            "caseId": cid,
            "nativeVerdict": "PASS" if res["passed"] else "FAIL",
            "nativeReason": res["reason"],
            "expected": res["expected"],
            "receiptChecks": len(checks),
            "receiptChecksFalse": sum(1 for c in checks if c[1] is False),
            "printedStatus": printed_status.get(cid),
            "filesInManifest": sum(1 for f in case_files if f in listed),
            "filesNotInManifest": [f for f in case_files if f not in listed],
            "native": json.loads(json.dumps(res, default=list)),
        })

    digest, files = input_digest(corpus)
    recount = {
        "population": len(records),
        "matched": sum(1 for r in records if r["nativeVerdict"] == "PASS"),
        "notMatched": [r["caseId"] for r in records if r["nativeVerdict"] != "PASS"],
        "receiptChecks": n_checks,
        "receiptChecksFalse": n_false,
        "printedStatusAgrees": all(
            (r["printedStatus"] == ("✓ PASS" if r["nativeVerdict"] == "PASS" else "✗ FAIL"))
            for r in records) and len(printed_status) == len(records),
        "casesWithFilesOutsideManifest": [r["caseId"] for r in records if r["filesNotInManifest"]],
    }
    result = {
        "label": label,
        "source": {"repository": "https://github.com/DSHCorrectover/ccs-conformance-vectors",
                   "commit": "effff90f231d11bb3be93d3d0d0792f36934cc78",
                   "checkerSHA256": sha((run / CHECKER).read_bytes()),
                   "command": ["python", CHECKER, CORPUS],
                   "pythonVersion": sys.version.split()[0],
                   "PYTHONHASHSEED": seed},
        "input": {"corpus": CORPUS, "digestRule":
                  "sha256(JCS({relative path: sha256(bytes)})) over every regular file in the corpus directory",
                  "inputDigest": digest, "fileCount": len(files),
                  "manifestSHA256": sha((corpus / "manifest.json").read_bytes()),
                  "manifestListedFiles": len(listed), "files": files},
        "nativeProcess": {"exitCode": proc.returncode, "stdoutSHA256": sha(proc.stdout),
                          "stderrSHA256": sha(proc.stderr), "printedFooter": footer,
                          "manifestCheckAccepted": manifest_ok,
                          "manifestErrors": manifest_errors},
        "recount": recount,
        "cases": records,
    }
    pathlib.Path(out).write_bytes(jcs.canonicalize(result))
    pathlib.Path(out).with_suffix(".stdout.txt").write_bytes(proc.stdout)
    print(label, "exit", proc.returncode, "|", " | ".join(footer), "| recount",
          f"{recount['matched']}/{recount['population']}", "| checks",
          n_checks, "false", n_false, "| digest", digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
