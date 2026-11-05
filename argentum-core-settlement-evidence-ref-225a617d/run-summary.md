# Run summary: settlement-evidence-ref at 225a617d

## Pin

- Pin as given and resolved: `225a617d4b21e47ed4f37d06177275f76dfb7e46`, tree
  `7c183225339f5d7bf3f69936b57342f46a0a9f55`.
- The default branch had moved to `d39821eee7ad9a47cc0a4137da20ca1fd9f40887` at run time.
  Between the two, `docs/spec/settlement-evidence-ref.md` differs in two lines (anchor
  links). `vectors.json` and `verify.py` are unchanged (`inputs/pin-vs-head-diffstat.txt`).
  The run is at the pin.

## Expected (as stated by the submitter)

- `python3 verify.py` with no arguments: 4/4.
- The inline artifact: `settlement_evidence_ref` =
  `f909081a79e81d6f5b3f914cf74c96cb51c764722bad012278d70b31f582c8a1`, computed as
  SHA-256(JCS(settlement_artifact)) with RFC 8785 key order by UTF-16 code units, and the
  project's own check rejects it because `transaction` is empty.

## Our reader

`reader/gk_reader.py` is built from `docs/spec/settlement-evidence-ref.md` and the
`comparator_rule` in `vectors.json`. It does not import or read `verify.py` or the
repository's `jcs.py`. The digest uses our own RFC 8785 canonicalizer (`reader/jcs.py`),
which sorts members by UTF-16 code units.

`runs/our-reader.txt`:

- Vectors: 4/4 agree on verdict and on all four checks (`ledger_recomputed`,
  `debit_credit_paired`, `matches_offer`, `transaction_present`), and all four digests match.
- Positive control: `settlement-matched-001` must PASS, and it does.
- Inline artifact: digest
  `f909081a79e81d6f5b3f914cf74c96cb51c764722bad012278d70b31f582c8a1`, equal to the expected
  value. It is the same JSON value as vector `settlement-transaction-missing-001`, and
  `transaction_present` is false.
- Canonicalizer control: the member order our canonicalizer produces for the sorting
  example of RFC 8785 section 3.2.3 equals the order given there. Code-point order would not.

## Project's verifier

- `runs/project-verify-py.txt` (Python 3.12.12): 4/4 passed, exit 0.
- `runs/project-verify-second-python.txt` (Python 3.9.6): exit 1 before any vector is read.
  The annotation `dict | None` at `verify.py:55` raises `TypeError` on Python 3.9. The
  instruction `python3 verify.py` therefore depends on which Python `python3` names.

## Observation on canonicalization

`verify.py` at the pin computes the digest with `json.dumps(obj, sort_keys=True, ...)`, which
orders keys by code point. The spec names UTF-16 code unit order. All keys in these vectors
and in the inline artifact are ASCII, where both orders coincide, so both methods give the
same four digests and the same inline digest. The vectors do not contain a case where the
two orders differ.

## What this run does not establish

- That any of the settlements happened. `ledger_recomputed` is a declaration carried in the
  vector, as the spec says. No ledger or RPC was read in this run, and the transaction
  references were not looked up.
- That `referenced_offer` corresponds to `offer_identity_ref`. The offer digest was not
  recomputed, because the offer bytes it is derived from are not part of the vectors.
- Behaviour of either canonicalizer on keys outside the Basic Multilingual Plane, beyond our
  own control case.
