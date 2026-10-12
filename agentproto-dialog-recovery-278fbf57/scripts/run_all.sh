#!/bin/bash
# Runs every configuration of agentproto-recovery @ 278fbf5 (v0.2.2) in its own process.
# usage: run_all.sh VARIANT    VARIANT = noseedA | noseedB | seed0
#   noseedX : no PYTHONHASHSEED (hash randomisation on, as in the author's runs)
#   seedN   : PYTHONHASHSEED=N (control only)
# All variants: env -i (clean env), python -P -s -B, PYTHONDONTWRITEBYTECODE=1 so
# that subprocesses started by the repo's restart harness write no bytecode either.
# TMPDIR points into .scratch (the harness itself hard-codes /tmp for its sockets).
set -u
T="/private/tmp/mt-runs/278fbf57"   # = /tmp/mt-runs/278fbf57 (canonical form, so pytest prints relative paths as before)
PY="$T/env/venv312/bin/python"
DRV="$T/scripts/driver.py"
OBS="$T/scripts/restart_observe_v1.py"   # noseedA/noseedB/seed0 ran with v1 in the earlier run
V="$1"
OUT="$T/runs/$V"
SCR="$T/.scratch/$V"
mkdir -p "$OUT/per-config" "$OUT/native" "$OUT/restart" "$SCR/tmp"
WORK=$(mktemp -d "$SCR/cwd-XXXX")   # empty cwd, nothing importable
cd "$WORK"
BASEENV=(PATH=/usr/bin:/bin HOME="$T/.scratch/home" TMPDIR="$SCR/tmp" PYTHONDONTWRITEBYTECODE=1)
# pytest only: plugin that keeps the machine name out of the JUnit XML hostname attribute
runpt() { local BASEENV=("${BASEENV[@]}" PYTHONPATH="$T/scripts/pytest_plugin"); run -m pytest -p junit_nohostname "$@"; }
case "$V" in
  seed*)   SEED="${V#seed}"
           run() { env -i "${BASEENV[@]}" PYTHONHASHSEED="$SEED" "$PY" -P -s -B "$@"; } ;;
  noseed*) run() { env -i "${BASEENV[@]}" "$PY" -P -s -B "$@"; } ;;
  *) echo "bad variant"; exit 2 ;;
esac

MANIFEST="$OUT/process-status.tsv"
printf "config\tpart\texit_code\tstarted_utc\tseconds\n" > "$MANIFEST"
one() {  # name part extra-args...
  local name="$1" part="$2"; shift 2
  local t0=$(date -u +%Y-%m-%dT%H:%M:%SZ) s=$SECONDS
  run "$DRV" "${name%+UNSAFE_GUESS}" "$part" "$OUT/per-config/$name.$part.jsonl" "$@" \
      > "$OUT/per-config/$name.$part.stdout" 2> "$OUT/per-config/$name.$part.stderr"
  local rc=$?
  printf "%s\t%s\t%s\t%s\t%s\n" "$name" "$part" "$rc" "$t0" "$((SECONDS-s))" >> "$MANIFEST"
}
for m in global-store global-endpoint scoped-store scoped-endpoint-noticket \
         scoped-endpoint-ticket scoped-endpoint-medticket; do
  one "$m" scenarios --repeats 3
  one "$m" faults --n 90 --seeds 1 2 3
done
# negative control, as in the repo's CLI (not one of the six configurations)
one "scoped-store+UNSAFE_GUESS" scenarios --unsafe --repeats 3 --only T05 T06
one "scoped-store+UNSAFE_GUESS" faults --unsafe --n 90 --seeds 1 2 3

# native CLI, default arguments (repeats 3, seeds 1 2 3, 90 dialogs, privacy 50)
for c in scenarios faults privacy; do
  run -m agentproto_recovery.cli "$c" --out "$OUT/native/$c" \
      > "$OUT/native/$c.stdout" 2> "$OUT/native/$c.stderr"
  printf "native-cli\t%s\t%s\t-\t-\n" "$c" "$?" >> "$MANIFEST"
done
# full test suite, cache plugin off so nothing is written into the repo
t0=$SECONDS
runpt -p no:cacheprovider -rA --junitxml "$OUT/native/pytest-junit.xml" \
    --basetemp "$SCR/pytest" --rootdir "$T/src/repo" "$T/src/repo/tests" \
    > "$OUT/native/pytest.stdout" 2> "$OUT/native/pytest.stderr"
printf "pytest\tall\t%s\t-\t%s\n" "$?" "$((SECONDS-t0))" >> "$MANIFEST"
# Agent A restart cases, observed (no assertions), 3 repeats
t0=$SECONDS
run "$OBS" "$T/src/repo" "$SCR/restart" "$OUT/restart/restart-observe.jsonl" --repeats 3 \
    > "$OUT/restart/restart-observe.stdout" 2> "$OUT/restart/restart-observe.stderr"
printf "restart-observe\tall\t%s\t-\t%s\n" "$?" "$((SECONDS-t0))" >> "$MANIFEST"
rmdir "$WORK" 2>/dev/null
cat "$MANIFEST"
