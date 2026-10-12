"""Input-byte digests per configuration, run 2 (278fbf5, v0.2.2).

Input of one configuration run = (a) the package source bytes that were
imported, (b) the driver, (c) the invocation arguments, (d) the fault
schedule the seeded RNG drew (read back from the records of the reference
variant noseedA). No tar of the foreign repo is kept; the git tree sha1, the
git-archive sha256 values and the two manifests identify the input instead.

usage: digests.py TAB_DIR
"""
import hashlib
import json
import sys
from pathlib import Path

T = Path(sys.argv[1])
REF = "noseedA"
CONFIGS = ["global-store", "global-endpoint", "scoped-store", "scoped-endpoint-noticket",
           "scoped-endpoint-ticket", "scoped-endpoint-medticket", "scoped-store+UNSAFE_GUESS"]


def h(b):
    return hashlib.sha256(b).hexdigest()


src = sorted((T / "src/repo/src/agentproto_recovery").glob("*.py"))
src_manifest = "".join(f"{h(p.read_bytes())}  src/agentproto_recovery/{p.name}\n" for p in src)
(T / "inputs/package-source.sha256").write_text(src_manifest)
arch = (T / "inputs/git-archive-sha256.txt").read_text().splitlines()
out = {
    "pinned_commit": "278fbf573522b6a45366c9e7f33a0235f4f715b8",
    "git_tree_sha1": (T / "inputs/git-tree-sha1.txt").read_text().strip(),
    "sha256_git_archive_tar_prefixed": arch[1],
    "sha256_git_archive_tar_no_prefix_installed": arch[3],
    "sha256_tracked_files_manifest": h((T / "inputs/tracked-files.sha256").read_bytes()),
    "tracked_files": len((T / "inputs/tracked-files.sha256").read_text().splitlines()),
    "sha256_package_source_manifest": h(src_manifest.encode()),
    "package_source_files": len(src),
    "sha256_driver_py": h((T / "scripts/driver.py").read_bytes()),
    "sha256_restart_observe_v1_py (noseedA, noseedB, seed0)": h((T / "scripts/restart_observe_v1.py").read_bytes()),
    "sha256_restart_observe_py (v2, extra-noseed)": h((T / "scripts/restart_observe.py").read_bytes()),
    "configs": {},
}
for c in CONFIGS:
    unsafe = c.endswith("+UNSAFE_GUESS")
    mode = c.removesuffix("+UNSAFE_GUESS")
    inv = {"scenarios": {"mode": mode, "unsafe": unsafe, "repeats": 3,
                         "only": ["T05", "T06"] if unsafe else None},
           "faults": {"mode": mode, "unsafe": unsafe, "n": 90, "seeds": [1, 2, 3]}}
    recs = [json.loads(l) for l in
            (T / f"runs/{REF}/per-config/{c}.faults.jsonl").read_text().splitlines()]
    sched = "\n".join(f"{r['seed']},{r['dialog']},{r['fault']}" for r in recs) + "\n"
    inv_b = json.dumps(inv, sort_keys=True, separators=(",", ":")).encode()
    out["configs"][c] = {
        "invocation": inv,
        "sha256_invocation_json": h(inv_b),
        "sha256_fault_schedule_seed,dialog,fault": h(sched.encode()),
        "sha256_input_bundle": h((out["sha256_package_source_manifest"]
                                  + out["sha256_driver_py"] + h(inv_b)).encode()),
    }
(T / "inputs/digests.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
print(json.dumps(out, indent=1, sort_keys=True))
