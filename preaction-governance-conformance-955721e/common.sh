# Shared helpers for the three REPRO-177 runs. Sourced by each run.sh.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=${WORK:-$HERE/../_work}
PY=${PY:-python3.12}          # Python >= 3.10 for the project scripts and our readers
PY39=${PY39:-/usr/bin/python3} # optional second interpreter, recorded if present
mkdir -p "$WORK/src" "$HERE/inputs" "$HERE/runs"

record_env() {
  {
    echo "run_started_utc: $(date -u +%FT%TZ)"
    echo "os: $(uname -srm)"
    command -v sw_vers >/dev/null && echo "macos: $(sw_vers -productVersion)"
    echo "python: $($PY --version 2>&1)"
    [ -x "$PY39" ] && echo "python_second: $($PY39 --version 2>&1)"
    command -v node >/dev/null && echo "node: $(node --version)"
    echo "git: $(git --version)"
  } > "$HERE/runs/environment.txt"
}

checkout() { # url pin name
  local url=$1 pin=$2 name=$3 d="$WORK/src/$3"
  [ -d "$d/.git" ] || git clone -q "$url" "$d"
  git -C "$d" fetch -q origin
  git -C "$d" -c advice.detachedHead=false checkout -q "$pin"
  {
    echo "repository: $url"
    echo "pin_as_given: $pin"
    echo "resolved_commit: $(git -C "$d" rev-parse HEAD)"
    echo "tree: $(git -C "$d" rev-parse 'HEAD^{tree}')"
    echo "commit_date: $(git -C "$d" show -s --format=%cI HEAD)"
    echo "default_branch_head_at_run: $(git ls-remote "$url" HEAD | cut -f1)"
  } > "$HERE/inputs/checkout.txt"
  echo "$d"
}

run_capture() { # outfile cmd...
  local out=$1; shift
  ( "$@" ) > "$HERE/runs/$out" 2>&1
  echo "exit=$?" >> "$HERE/runs/$out"
}
