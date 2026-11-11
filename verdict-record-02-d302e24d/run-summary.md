# Run summary: draft-wright-verdict-record-02 vectors at d302e24d

## Pins

- Draft: `draft-wright-verdict-record-02`, fetched from
  `https://www.ietf.org/archive/id/draft-wright-verdict-record-02.txt`, SHA-256
  `91ad251baca9537d5764288dffabe214fe433cea11e69f7ea987baea12622b64` (`inputs/draft.txt`).
- Vectors: `diggertydog/verdict-record-test-vectors` at
  `d302e24d2114f0a397496cdec37e9fac8a14816d`, tree `a7adcea51ced6f100f35a304fb562e23ed2e2d42`.
  This was the default-branch head at both phases (`inputs/checkout-vectors*.txt`).
- Cases: 71 vector files `[a-h]NN-*.json` at the top of that repository. Their SHA-256 values
  are in `inputs/vector-files.sha256`.
- Our checker: `checker/vrc.py`, SHA-256 in `inputs/checker-files.sha256` and `run.json`.
- `receiver_provenance`: `clean_room` (see `README.md` and `PHASE1.md`).
- Environment: macOS 26.6.2 arm64, CPython 3.12.12, standard library only
  (`runs/environment-*.txt`).

## Appendix A.2, recomputed from the draft text

`checker/a2_from_text.py` reads the three artwork blocks of A.2 from the draft text. It undoes
the RFC 8792 folding, removes the page breaks and forms the record's canonical bytes under
Section 2.1. Output: `runs/ours-a2-from-text.txt`.

| Value | Computed | Stated in A.2 | Equal |
|---|---|---|---|
| Verdict record, canonical bytes | `62017940a8ddddd5ddd7ff46c8ff2a6ce79dfcccb775d767b8dff8db0ebe19ed` | `62017940…19ed` | yes |
| Parent hop, evidence item 0 | `1336337e88adc67853b80b4998363210dc5c0797cc7b7c722128cecc56a38c14` | `1336337e…8c14` | yes |
| Child hop, evidence item 1 | `8886795d4403b5cd8820eb813ee0724f1d6d5d383124364b09cdc5020639e00c` | `8886795d…e00c` | yes |

Both hops are already in canonical form, as A.2 says they are.

The record was checked under our own policy, which reads inputs from evidence only:
`{"formats":["https://datatracker.ietf.org/doc/draft-durga-agenttrust-trace-verification/"],"inputs_from_evidence_only":true,"judgement_kinds":[],"max_depth":0}`,
SHA-256 over its canonical form `f8f3653081eeaff344cce03a0d9c1a73a263502c6e672315f2f93f3823bed0e5`.
The upper time bound `2026-11-02T00:00:00.000000Z` is our own input; no container is in
this run.

- Hop format requires a signature: **held**. Step 1 PASS, step 2 NOT RUN (both entries: no
  signature, which the format requires), step 3 NOT RUN (all four inputs are bound to entries
  that step 2 does not rely on). The check is NOT RUN at step 2. This is what A.2 predicts.
- Hop format read without a signature (parse only): **released**, steps PASS / PASS / PASS,
  as A.2 predicts for a checker that verifies the hops without a signature.

## All 71 cases

Per case, with every step and each step's notes: `runs/ours-vectors.jsonl`. Summary lines as
printed: `runs/ours-vectors.txt`.

Our checker: 13 released, 14 held, 39 refused, 5 no verdict. Our policy digest equals the
vector's `policy_sha256` in 71 of 71 cases, and the record digest equals `record_sha256` in
71 of 71.

Reference checker (`vrcheck.py` at the pin, run after phase 1 was committed), as printed by
`run_all.py`: "vectors run 71, agreeing 71", exit 0 (`runs/reference-run_all.txt`).
Recount from its per-case reports (`runs/reference-vrcheck.txt`) against the vectors'
expected answers: it differs in 0 cases.

Comparison (`runs/comparison.txt`, `runs/comparison.json`):

- state equal in 69 of 71 cases;
- all three step results equal in 68 of 71;
- the inputs named as read from body and the evidence entries step 2 does not rely on are
  equal in every case where both checkers ran the steps.

An absent `body_inputs_read` and an empty one are compared as equal.

| Case | Ours: state | Ours: steps 1 / 2 / 3 | Reference: state | Reference: steps 1 / 2 / 3 |
|---|---|---|---|---|
| a01-baseline-released | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| a02-whitespace | refused | (no step ran) | refused | (no step ran) |
| a03-member-order | refused | (no step ran) | refused | (no step ran) |
| a04-duplicate-member | refused | (no step ran) | refused | (no step ran) |
| a05-byte-order-mark | refused | (no step ran) | refused | (no step ran) |
| a06-fraction | refused | (no step ran) | refused | (no step ran) |
| a07-integer-range | refused | (no step ran) | refused | (no step ran) |
| a08-escaped-non-ascii | refused | (no step ran) | refused | (no step ran) |
| a09-utf8-bytes | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| a10-lone-surrogate | refused | (no step ran) | refused | (no step ran) |
| a11-depth-32 | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| a12-depth-33 | refused | (no step ran) | refused | (no step ran) |
| a13-unknown-member | refused | (no step ran) | refused | (no step ran) |
| a14-missing-writer | refused | (no step ran) | refused | (no step ran) |
| b01-check-missing | refused | FAIL / PASS / NOT RUN | refused | FAIL / PASS / NOT RUN |
| b02-check-no-result | refused | FAIL / PASS / NOT RUN | refused | FAIL / PASS / NOT RUN |
| b03-judgement-kind-not-listed | refused | FAIL / PASS / PASS | refused | FAIL / PASS / PASS |
| b04-judgement-kind-listed | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| c01-evidence-missing | refused | PASS / FAIL / PASS | refused | PASS / FAIL / PASS |
| c02-entry-extra-member | refused | PASS / FAIL / PASS | refused | PASS / FAIL / PASS |
| c03-entry-uppercase-hex | refused | PASS / FAIL / PASS | refused | PASS / FAIL / PASS |
| c04-item-not-held | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c05-format-not-in-policy | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c06-item-does-not-verify | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c07-cites-released-record | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| c08-beyond-depth | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c09-cited-bound-later | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c10-cites-refused-record | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| c11-claim-ref-not-in-evidence | refused | (no step ran) | refused | PASS / FAIL / PASS |
| c12-empty-evidence | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| d01-result-mismatch | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| d02-input-wrong-type | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| d03-rule-not-held | held | PASS / PASS / NOT RUN | held | PASS / PASS / NOT RUN |
| d04-not-run-then-fail | refused | PASS / NOT RUN / FAIL | refused | PASS / NOT RUN / FAIL |
| d05-rule-false-low | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| e01-invalid-policy | no verdict | (no step ran) | no verdict | (no step ran) |
| f01-appendix-a | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| g01-bound-pointer-released | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| g02-bound-digest-released | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| g03-body-inputs-named | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| g04-evidence-only-body-input | held | PASS / PASS / NOT RUN | held | PASS / PASS / NOT RUN |
| g05-evidence-only-bound | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| g06-bound-item-not-held | held | PASS / NOT RUN / NOT RUN | held | PASS / NOT RUN / NOT RUN |
| g07-bound-item-not-relied-on | held | PASS / NOT RUN / NOT RUN | held | PASS / NOT RUN / NOT RUN |
| g08-binding-extra-member | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| g09-no-such-evidence-entry | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| g10-pointer-does-not-resolve | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| g11-item-not-json | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| g12-not-run-and-fail | refused | PASS / NOT RUN / FAIL | refused | PASS / NOT RUN / FAIL |
| g13-bound-input-wrong-type | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| g14-policy-evidence-only-not-boolean | no verdict | (no step ran) | no verdict | (no step ran) |
| g15-policy-unknown-member | no verdict | (no step ran) | released | PASS / PASS / PASS |
| g16-policy-citation-depth | no verdict | (no step ran) | released | PASS / PASS / PASS |
| g17-policy-two-depths | no verdict | (no step ran) | no verdict | (no step ran) |
| g18-step2-names-every-entry | held | PASS / NOT RUN / PASS | held | PASS / NOT RUN / PASS |
| g19-act-time-form | refused | (no step ran) | refused | (no step ran) |
| g20-version-zero | refused | (no step ran) | refused | (no step ran) |
| g21-supersedes-on-version-1 | refused | (no step ran) | refused | (no step ran) |
| g22-version-2-supersedes-null | refused | (no step ran) | refused | (no step ran) |
| g23-version-2-supersedes-digest | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| g24-key-empty | refused | (no step ran) | refused | (no step ran) |
| g25-actor-person-with-model | refused | (no step ran) | refused | (no step ran) |
| g26-v-other-value | refused | (no step ran) | refused | (no step ran) |
| g27-check-extra-member | refused | FAIL / PASS / PASS | refused | FAIL / PASS / PASS |
| g28-claim-text-and-ref | refused | (no step ran) | refused | (no step ran) |
| g29-body-not-object | refused | (no step ran) | refused | (no step ran) |
| g30-claim-text-not-string | refused | (no step ran) | refused | (no step ran) |
| h01-a2-hops-without-signature-released | released | PASS / PASS / PASS | released | PASS / PASS / PASS |
| h02-a2-hops-signature-required-held | held | PASS / NOT RUN / NOT RUN | held | PASS / NOT RUN / NOT RUN |
| h03-a2-child-widened-refused | refused | PASS / PASS / FAIL | refused | PASS / PASS / FAIL |
| h04-a2-child-not-held | held | PASS / NOT RUN / NOT RUN | held | PASS / NOT RUN / NOT RUN |

## Differences from the reference checker

Each difference is given with the case, the step and the bytes.

**c11-claim-ref-not-in-evidence.**
- Ours: refused before any step, no step result.
- Reference: refused, step 1 PASS, step 2 FAIL, step 3 PASS; `body_inputs_read`
  `["min","value"]`.
- Record bytes in `runs/comparison.json`, SHA-256 `6954663665c1594e7268072c24c056b12341ab48f972799bad6b403722a8c035`. The members that differ in role
  are `body.claim.ref`, `{"format":"urn:example:verdict-record:format:opaque","sha256":"a35bef50834cbeb199528f8480fc77d41f2caf9059f74708cc9edb35c9964e82"}`,
  and `evidence`, `[{"format":"urn:example:verdict-record:format:opaque","sha256":"e3bf3a3fcd5b95e78cf1303f9ee301d97032271dd218f038e1a2c8265bd1d56d"}]`.
- The vector's expected answer gives the state, `refused`, and no step results.

**g15-policy-unknown-member.**
- Ours: no verdict, no step result.
- Reference: released, steps PASS / PASS / PASS.
- Policy bytes (canonical form):
  `{"formats":["urn:example:verdict-record:format:opaque","urn:example:verdict-record:format:never-verifies","verdict-record/1"],"judgement_kinds":["model-decision"],"max_depth":2,"max_evidence_age_seconds":3600}`.

**g16-policy-citation-depth.**
- Ours: no verdict, no step result.
- Reference: released, steps PASS / PASS / PASS.
- Policy bytes (canonical form):
  `{"citation_depth":0,"formats":["urn:example:verdict-record:format:opaque"],"judgement_kinds":["model-decision"]}`.

Our checker differs from the vectors' expected answers in g15 and g16 only.

## Readings our checker takes

Phase 1 fixed these where the -02 text leaves a choice open. Each is marked `READING` in
`checker/vrc.py`, or follows from the code at the place named.

1. Control characters in canonical form are escaped as `\b \t \n \f \r`, or as `\u00XX` in
   lowercase hex. No vector exercises this.
2. A time must also be a real calendar time.
3. `body.claim` is required. A broken claim, including a `ref` that does not also appear in
   `evidence`, is a break of Section 2.2 in body and is refused before any step.
4. A `v` other than `"verdict-record/1"` is refused before any step. Any string `kind` is
   read. `supersedes` may be absent. The values inside `actor` are not type-checked.
5. Policy: the member names are the vectors' (`judgement_kinds`, `formats`, `max_depth`,
   `inputs_from_evidence_only`). A member the checker does not know makes the policy invalid,
   as does a non-boolean `inputs_from_evidence_only`.
6. An item read through a pointer is parsed under the strict-JSON rules and the nesting
   limit, not under the record's integer-only rule.
7. A format the policy lists but the checker holds no rules for is not relied on.
8. An item whose own upper time bound cannot be compared with the citing record's bound is
   not relied on.
9. If the checker does not hold the rule, step 3 is NOT RUN without resolving the inputs.
   Within step 3, any FAIL outranks any NOT RUN. A missing or malformed `check` leaves step 3
   NOT RUN.
10. For the rule `judgement`, step 3 PASSes. An empty `evidence` array PASSes step 2.
11. Step 2 names every entry it does not rely on.
12. `body_inputs_read` is reported under the default policy only (Section 4.4).
13. The hop format of A.2 is held under one of two readings, chosen by the vector's `hold`
    list. `signature_required`: no hop verifies, since none carries a signature and this
    checker holds no rule for verifying one. `parse_only`: a hop verifies when it parses as a
    strict JSON object. The A.2 rule is implemented from the text of A.2.

## Order of work, and runs of phase 2

- Phase 1 was committed and pushed (`64c0c1d`, GitHub push 2026-11-11T17:41:04Z) before any
  file of the reference checker was opened.
- Phase 2 ran three times, from 17:42 to 17:43:40Z. Between runs only `checker/compare.py`
  and `run-reference.sh` changed:
  - an absent and an empty `body_inputs_read` are now compared as equal;
  - a recount of the reference against the expected answers was added;
  - `run-reference.sh` no longer appends to a phase-1 file.
- The reference outputs were the same in every run. The files here are those of the last
  run.

## What this run does not establish

- Signing and containers (Section 3). The vectors supply each upper time bound directly.
- The proposal cases (`proposals/`) and the one chain interop case (`interop/one-chain`). They
  were not run. The first tests proposed extensions, not -02. The second needs checkouts of
  two further repositories.
- The format rules of `draft-durga-agenttrust-trace-verification`. Our two hop readings stand
  in for them, as the vectors' `held/` modules do on the reference side.
- That the -02 text is unambiguous where the two checkers agree. Agreement on 68 cases shows
  the same outputs, not one reading of the text.
- That the vectors cover every requirement of -02.
