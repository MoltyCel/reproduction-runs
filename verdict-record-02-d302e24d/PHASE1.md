# Phase 1: our result per case, fixed before the reference checker

This commit holds our checker, its inputs and its outputs only. The reference checker
of the vectors repository (`vrcheck.py`, `run_all.py`) has not been read or run at
this commit, nor has `blind-checker.py`, `DUTIES.md`, any module under `held/`,
`interop/`, `proposals/` or `handoff-record-replay/`, or the README past line 82.

Read before this commit, from the vectors repository at
`d302e24d2114f0a397496cdec37e9fac8a14816d`:

- the file list and `git log --stat` of the last three commits (file names only);
- `README.md` lines 1-82: the vector file format, what the checker holds, the
  test-only evidence formats and the test-only rules;
- the 71 vector files `[a-h]NN-*.json`. Our runner passes only the checker inputs
  to the checker (`record_b64`, `evidence_items`, `upper_time_bound`, `policy`,
  `hold`); it does not read `expected`. The vector files were opened while writing
  the runner, and the `expected` member of two of them (a01, h02) was seen then.

Outputs: `runs/ours-vectors.jsonl` (one line per case), `runs/ours-vectors.txt`
(summary lines as printed), `runs/ours-a2-from-text.txt` (Appendix A.2 recomputed
from the draft text). The comparison with the reference checker follows in a later
commit.
