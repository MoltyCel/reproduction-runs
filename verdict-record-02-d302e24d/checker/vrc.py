"""A checker for draft-wright-verdict-record-02, written from the text of the draft alone.

Source: https://www.ietf.org/archive/id/draft-wright-verdict-record-02.txt
(SHA-256 of the fetched bytes in inputs/draft.sha256). Section numbers in comments refer
to that text. The test-only rules and formats come from the section "Vector file format",
"Test-only evidence formats" and "Test-only rules" of the vectors' README. Nothing in this
file was taken from the reference checker or from any module of the vectors repository.

Where -02 leaves a choice open, the reading taken here is marked READING and listed in
run-summary.md. Standard library only.
"""
import base64
import datetime
import hashlib
import json
import re

TEXT = "draft-wright-verdict-record-02"
V1 = "verdict-record/1"
MAX_INT = 2 ** 53 - 1
MAX_LEVELS = 32
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\Z")
INT_TOKEN = re.compile(r"-?(0|[1-9][0-9]*)\Z")

RULE_AT_LEAST = "urn:example:verdict-record:rule:at-least"
RULE_EQUALS = "urn:example:verdict-record:rule:equals"
RULE_A2 = "urn:example:verdict-record:rule:hop-continuity-attenuation:v1"
FMT_OPAQUE = "urn:example:verdict-record:format:opaque"
FMT_NEVER = "urn:example:verdict-record:format:never-verifies"
FMT_HOP = "https://datatracker.ietf.org/doc/draft-durga-agenttrust-trace-verification/"

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT RUN"


class Refused(Exception):
    """Bytes or members broken before any step runs (Section 2.1, last paragraph)."""


class NotJSON(Exception):
    pass


# ---------------------------------------------------------------- Section 2.1

def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def sha256_hex(b):
    return hashlib.sha256(b).hexdigest()


def _no_dupes(pairs):
    names = [k for k, _ in pairs]
    if len(set(names)) != len(names):
        raise NotJSON("an object has the same member name twice")
    return dict(pairs)


def _bad_constant(name):
    raise NotJSON("not a JSON number: %s" % name)


class _Float(float):
    pass


def _levels(x):
    if isinstance(x, dict):
        return 1 + max([_levels(v) for v in x.values()], default=0)
    if isinstance(x, list):
        return 1 + max([_levels(v) for v in x], default=0)
    return 0


def _has_surrogate(x):
    if isinstance(x, str):
        return any(0xD800 <= ord(c) <= 0xDFFF for c in x)
    if isinstance(x, dict):
        return any(_has_surrogate(k) or _has_surrogate(v) for k, v in x.items())
    if isinstance(x, list):
        return any(_has_surrogate(v) for v in x)
    return False


def parse_strict(b, integers_only):
    """Strict JSON of Section 2.1, second paragraph, plus the nesting limit.

    integers_only adds the number rules of the third paragraph (records). For an
    evidence item read through a pointer, READING: the strict-JSON paragraph and the
    nesting limit apply, the integer-only number rule (part of canonical form) does not.
    """
    if b.startswith(b"\xef\xbb\xbf"):
        raise NotJSON("starts with a byte-order mark")
    try:
        s = b.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise NotJSON("not valid UTF-8")
    floats = []

    def pf(tok):
        floats.append(tok)
        return _Float(tok)

    try:
        x = json.loads(s, object_pairs_hook=_no_dupes, parse_constant=_bad_constant,
                       parse_float=pf)
    except NotJSON:
        raise
    except (ValueError, RecursionError) as e:
        raise NotJSON("not JSON: %s" % type(e).__name__)
    if _has_surrogate(x):
        raise NotJSON("an escape forms a lone surrogate")
    if _levels(x) > MAX_LEVELS:
        raise NotJSON("nested deeper than 32 levels")
    if integers_only:
        if floats:
            raise NotJSON("a number with a fraction or exponent: %s" % floats[0])
        bad = _out_of_range(x)
        if bad is not None:
            raise NotJSON("an integer outside -(2^53-1)..2^53-1: %d" % bad)
    return x


def _out_of_range(x):
    if is_int(x):
        return x if abs(x) > MAX_INT else None
    vals = x.values() if isinstance(x, dict) else x if isinstance(x, list) else []
    for v in vals:
        r = _out_of_range(v)
        if r is not None:
            return r
    return None


def _esc(s):
    out = ['"']
    for c in s:
        o = ord(c)
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif o < 0x20:
            # READING: -02 says control characters are escaped but not how. Short forms
            # where JSON has one, else \u00XX in lowercase hex.
            out.append({8: "\\b", 9: "\\t", 10: "\\n", 12: "\\f", 13: "\\r"}.get(o, "\\u%04x" % o))
        else:
            out.append(c)
    out.append('"')
    return "".join(out)


def canonical(x):
    """Canonical form of Section 2.1, as bytes."""
    def ser(v):
        if v is None:
            return "null"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if is_int(v):
            return str(v)
        if isinstance(v, float):
            raise ValueError("canonical form has integers only")
        if isinstance(v, str):
            return _esc(v)
        if isinstance(v, list):
            return "[" + ",".join(ser(e) for e in v) + "]"
        if isinstance(v, dict):
            # sorted by name, compared as sequences of Unicode code points
            return "{" + ",".join(_esc(k) + ":" + ser(v[k]) for k in sorted(v)) + "}"
        raise ValueError(type(v))
    return ser(x).encode("utf-8")


def is_time(x):
    if not isinstance(x, str) or not TIME.match(x):
        return False
    try:
        datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return False  # READING: a time must also be a real calendar time
    return True


def is_entry(e):
    """An evidence entry of Section 2.2: exactly sha256 and format."""
    return (isinstance(e, dict) and set(e) == {"sha256", "format"}
            and isinstance(e["sha256"], str) and HEX64.match(e["sha256"]) is not None
            and isinstance(e["format"], str))


# ---------------------------------------------------------------- Section 2.2, 2.3

ALLOWED = {"v", "kind", "key", "version", "supersedes", "writer", "actor", "act_time",
           "evidence", "check", "body"}
REQUIRED = ("v", "kind", "key", "version", "writer", "body")


def parse_record(b):
    """Returns the parsed record or raises Refused naming the rule broken."""
    try:
        r = parse_strict(b, integers_only=True)
    except NotJSON as e:
        raise Refused("2.1: %s" % e)
    if not isinstance(r, dict):
        raise Refused("2.1: a verdict record is a JSON object")
    if canonical(r) != b:
        raise Refused("2.1: re-serializing the parsed record does not give the same bytes")
    extra = sorted(set(r) - ALLOWED)
    if extra:
        raise Refused("2.2: member not allowed: %s" % ", ".join(extra))
    for m in REQUIRED:
        if m not in r:
            raise Refused("2.2: required member missing: %s" % m)
    if r["v"] != V1:
        # READING: this document defines only "verdict-record/1"
        raise Refused("2.2: v is not \"verdict-record/1\"")
    if not isinstance(r["kind"], str):
        raise Refused("2.2: kind is not a string")
    if not isinstance(r["key"], str) or r["key"] == "":
        raise Refused("2.2: key is not a non-empty string")
    if not is_int(r["version"]) or r["version"] < 1:
        raise Refused("2.2: version is not an integer of 1 or more")
    if "supersedes" in r:
        s = r["supersedes"]
        if r["version"] == 1 and s is not None:
            raise Refused("2.2: supersedes is not null for version 1")
        if r["version"] > 1 and not (isinstance(s, str) and HEX64.match(s)):
            raise Refused("2.2: supersedes is not a digest for a later version")
    if not isinstance(r["writer"], str) or r["writer"] == "":
        raise Refused("2.2: writer is not a non-empty string")
    if "actor" in r:
        a = r["actor"]
        if not isinstance(a, dict) or a.get("type") not in ("person", "system"):
            raise Refused("2.2: actor is not an object with type person or system")
        want = {"type", "id"} if a["type"] == "person" else {"type", "id", "model", "model_version"}
        if set(a) != want:
            raise Refused("2.2: actor of type %s has members %s" % (a["type"], sorted(a)))
    if "act_time" in r and not is_time(r["act_time"]):
        raise Refused("2.1: act_time is not a time YYYY-MM-DDTHH:MM:SS.ffffffZ")
    body = r["body"]
    if not isinstance(body, dict):
        raise Refused("2.2: body is not an object")
    # READING: the claim lives in body (2.2 "It holds the claim"), so a broken claim is a
    # break of 2.2 other than in evidence and check, refused before any step.
    if "claim" not in body:
        raise Refused("2.3: body.claim missing")
    c = body["claim"]
    if not isinstance(c, dict) or len(c) != 1 or not (set(c) <= {"text", "ref"}):
        raise Refused("2.3: body.claim is not an object with exactly one of text or ref")
    if "text" in c and not isinstance(c["text"], str):
        raise Refused("2.3: body.claim.text is not a string")
    if "ref" in c:
        if not is_entry(c["ref"]):
            raise Refused("2.3: body.claim.ref is not an evidence entry")
        ev = r.get("evidence")
        if not (isinstance(ev, list) and c["ref"] in ev):
            raise Refused("2.3: body.claim.ref does not also appear in evidence")
    return r


# ---------------------------------------------------------------- Section 4.5

POLICY_MEMBERS = {"judgement_kinds", "formats", "max_depth", "inputs_from_evidence_only"}


def policy_problem(p):
    """None when the policy is valid, else the reason. Member names are the vectors'
    (README, "Vector file format"); -02 names none."""
    if not isinstance(p, dict):
        return "policy is not an object"
    extra = sorted(set(p) - POLICY_MEMBERS)
    if extra:
        # READING: a statement this checker does not know cannot be applied; such a
        # policy is not one of the forms Section 4.5 lists.
        return "policy states a member this checker does not know: %s" % ", ".join(extra)
    for m in ("judgement_kinds", "formats", "max_depth"):
        if m not in p:
            return "policy lacks %s" % m
    for m in ("judgement_kinds", "formats"):
        if not isinstance(p[m], list) or not all(isinstance(x, str) for x in p[m]):
            return "policy %s is not a list of strings" % m
    if not is_int(p["max_depth"]) or p["max_depth"] < 0:
        return "policy max_depth is not an integer of 0 or more"
    if "inputs_from_evidence_only" in p and not isinstance(p["inputs_from_evidence_only"], bool):
        # READING: the fourth statement in a form other than a boolean is invalid too.
        return "policy inputs_from_evidence_only is not a boolean"
    return None


# ---------------------------------------------------------------- held specifications

class Holdings:
    """What the checker holds as its own input (Section 4.2): rule specifications and
    format rules. Always: the test-only rules and formats. Per vector: what `hold` names.
    The A.2 rule and both hop-format readings are implemented here from the draft text
    and the names in the README, not from the modules of the vectors repository."""

    def __init__(self, hold):
        self.rules = {RULE_AT_LEAST, RULE_EQUALS}
        self.hop_reading = None
        for h in hold:
            if h == "appendix_a2_rule.py":
                self.rules.add(RULE_A2)
            elif h == "appendix_a2_hops_parse_only.py":
                self.hop_reading = "parse_only"
            elif h == "appendix_a2_hops_signature_required.py":
                self.hop_reading = "signature_required"
            else:
                raise ValueError("unknown holding %s" % h)

    def describe(self):
        d = sorted(self.rules) + [FMT_OPAQUE, FMT_NEVER, V1]
        if self.hop_reading:
            d.append("%s (reading: %s)" % (FMT_HOP, self.hop_reading))
        return d


def run_rule(rule, inputs):
    """Returns ("ok", result) or ("type", reason) or ("inputs", reason)."""
    if rule == RULE_AT_LEAST:
        if set(inputs) != {"value", "min"}:
            return "inputs", "at-least takes exactly value and min"
        if not (is_int(inputs["value"]) and is_int(inputs["min"])):
            return "type", "at-least inputs are not integers"
        return "ok", "pass" if inputs["value"] >= inputs["min"] else "fail"
    if rule == RULE_EQUALS:
        if set(inputs) != {"a", "b"}:
            return "inputs", "equals takes exactly a and b"
        return "ok", "equal" if json_equal(inputs["a"], inputs["b"]) else "different"
    if rule == RULE_A2:
        # -02 Appendix A.2: exactly four inputs
        if set(inputs) != {"parent_hash", "parent_digest", "parent_scopes", "child_scopes"}:
            return "inputs", "the A.2 rule takes exactly four inputs"
        for n in ("parent_hash", "parent_digest"):
            if not isinstance(inputs[n], str):
                return "type", "%s is not a string" % n
        for n in ("parent_scopes", "child_scopes"):
            v = inputs[n]
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                return "type", "%s is not an array of strings" % n
        ok = (inputs["parent_hash"] == inputs["parent_digest"]
              and all(c in inputs["parent_scopes"] for c in inputs["child_scopes"]))
        return "ok", "attenuated_and_linked" if ok else "not_attenuated_or_not_linked"
    raise KeyError(rule)


def json_equal(a, b):
    if is_int(a) and is_int(b):
        return a == b
    if type(a) is not type(b) and not (isinstance(a, float) and isinstance(b, float)):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    return a == b


def verify_item(fmt, item_bytes, holdings):
    """Format rules other than verdict-record/1. Returns (verifies, reason)."""
    if fmt == FMT_OPAQUE:
        return True, None
    if fmt == FMT_NEVER:
        return False, "the format's rules are not met"
    if fmt == FMT_HOP and holdings.hop_reading == "parse_only":
        try:
            x = parse_strict(item_bytes, integers_only=False)
        except NotJSON as e:
            return False, "hop record does not parse: %s" % e
        return (True, None) if isinstance(x, dict) else (False, "hop record is not an object")
    if fmt == FMT_HOP and holdings.hop_reading == "signature_required":
        # The hop format requires a signature (-02 A.2). This checker holds no rule to
        # verify one, so an item verifies under this reading only if that were possible.
        try:
            x = parse_strict(item_bytes, integers_only=False)
        except NotJSON:
            x = None
        if isinstance(x, dict) and "signature" in x:
            return False, "carries a signature this checker holds no rule to verify"
        return False, "carries no signature, which the format requires"
    return False, "the checker holds no rules for this format"


# ---------------------------------------------------------------- Section 4

def resolve_pointer(doc, ptr):
    """RFC 6901. Returns (True, value) or (False, None)."""
    if not isinstance(ptr, str):
        return False, None
    if ptr == "":
        return True, doc
    if not ptr.startswith("/"):
        return False, None
    cur = doc
    for raw in ptr[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            return False, None
        tok = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict):
            if tok not in cur:
                return False, None
            cur = cur[tok]
        elif isinstance(cur, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", tok) or int(tok) >= len(cur):
                return False, None
            cur = cur[int(tok)]
        else:
            return False, None
    return True, cur


class Checker:
    def __init__(self, policy, items, holdings):
        self.policy = policy
        self.holdings = holdings
        # items held, by digest: bytes and the upper time bound their verification gives
        self.items = {}
        for it in items:
            b = base64.b64decode(it["b64"], validate=True)
            self.items[sha256_hex(b)] = (b, it.get("upper_time_bound"))
        self.evidence_only = policy.get("inputs_from_evidence_only") is True

    def check(self, record_bytes, upper_time_bound, depth=0):
        rep = {"record_sha256": sha256_hex(record_bytes), "depth": depth,
               "upper_time_bound": upper_time_bound}
        try:
            r = parse_record(record_bytes)
        except Refused as e:
            rep.update(state="refused", refused_before_steps=str(e), steps=None)
            return rep
        steps = {}
        s1, n1 = self.step1(r)
        s2, n2, relied = self.step2(r, upper_time_bound, depth)
        s3, n3, body_read = self.step3(r, relied)
        steps = {"1": s1, "2": s2, "3": s3}
        rep["steps"] = steps
        rep["step_notes"] = {k: v for k, v in (("1", n1), ("2", n2), ("3", n3)) if v}
        if not self.evidence_only:
            rep["body_inputs_read"] = body_read  # Section 4.4, default policy
        res = [s1, s2, s3]
        if FAIL in res:
            rep["state"] = "refused"
            rep["check"] = "FAIL at step %d" % (max(i for i, s in enumerate(res) if s == FAIL) + 1)
        elif NOT_RUN in res:
            rep["state"] = "held"
            rep["check"] = "NOT RUN at step %d" % (res.index(NOT_RUN) + 1)
        else:
            rep["state"] = "released"
            rep["check"] = "PASS"
        return rep

    # Step 1
    def step1(self, r):
        if "check" not in r:
            return FAIL, ["check is missing"]
        c = r["check"]
        if not isinstance(c, dict):
            return FAIL, ["check is not an object"]
        extra = sorted(set(c) - {"rule", "inputs", "result"})
        if extra:
            return FAIL, ["check has a member not allowed: %s" % ", ".join(extra)]
        if "rule" not in c or not isinstance(c["rule"], str):
            return FAIL, ["check names no rule"]
        if "result" not in c:
            return FAIL, ["check gives no result"]
        if c["rule"] == "judgement" and r["kind"] not in self.policy["judgement_kinds"]:
            return FAIL, ["judgement is not allowed for kind %s" % r["kind"]]
        return PASS, None

    # Step 2
    def step2(self, r, upper, depth):
        """Returns (result, notes, relied) where relied is the set of entry indexes
        the step relies on."""
        if "evidence" not in r:
            return FAIL, ["evidence is missing"], set()
        ev = r["evidence"]
        if not isinstance(ev, list):
            return FAIL, ["evidence is not an array"], set()
        for i, e in enumerate(ev):
            if not is_entry(e):
                return FAIL, ["evidence entry %d is not an entry as in Section 2.2" % i], set()
        notes, relied = [], set()
        for i, e in enumerate(ev):
            why = self._entry(e, upper, depth)
            if why is None:
                relied.add(i)
            else:
                notes.append("entry %d (%s): %s" % (i, e["sha256"], why))
        return (NOT_RUN if notes else PASS), (notes or None), relied

    def _entry(self, e, upper, depth):
        held = self.items.get(e["sha256"])
        if held is None:
            return "no item held with this digest"
        b, item_upper = held
        if e["format"] not in self.policy["formats"]:
            return "format not listed in the checker's policy"
        if e["format"] == V1:
            if depth + 1 > self.policy["max_depth"]:
                return "cited verdict record beyond the policy's citation depth"
            sub = self.check(b, item_upper, depth + 1)
            if sub["state"] != "released":
                return "cited verdict record is %s" % sub["state"]
        else:
            ok, why = verify_item(e["format"], b, self.holdings)
            if not ok:
                return "does not verify: %s" % why
        if item_upper is not None:
            if not is_time(item_upper):
                return "item's upper time bound is not a time"
            # READING: with no upper time bound for the citing record, the comparison
            # cannot be made, so the item is not relied on.
            if upper is None or item_upper > upper:
                return "item's upper time bound is later than the record's"
        return None

    # Step 3
    def step3(self, r, relied):
        c = r.get("check")
        if not (isinstance(c, dict) and isinstance(c.get("rule"), str) and "result" in c):
            return NOT_RUN, ["needs check.rule and check.result"], []
        rule = c["rule"]
        if rule == "judgement":
            return PASS, None, []
        if rule not in self.holdings.rules:
            return NOT_RUN, ["needs the specification of rule %s" % rule], []
        inputs = c.get("inputs", {})
        if not isinstance(inputs, dict):
            return FAIL, ["check.inputs is not an object"], []
        fails, notruns, values, body_read = [], [], {}, []
        ev = r.get("evidence") if isinstance(r.get("evidence"), list) else None
        for name in sorted(inputs):
            src = inputs[name]
            if isinstance(src, str):
                if self.evidence_only:
                    notruns.append("input %s is read from body; the policy reads inputs from evidence only" % name)
                    continue
                if src not in r["body"]:
                    fails.append("input %s: no member %s in body" % (name, src))
                    continue
                values[name] = r["body"][src]
                body_read.append(name)
            elif isinstance(src, dict):
                if "evidence" not in src or set(src) - {"evidence", "pointer"}:
                    fails.append("input %s: binding object with another member" % name)
                    continue
                idx = src["evidence"]
                if not is_int(idx):
                    fails.append("input %s: evidence index is not an integer" % name)
                    continue
                if ev is None or not (0 <= idx < len(ev)):
                    fails.append("input %s: no evidence entry %d" % (name, idx))
                    continue
                entry = ev[idx]
                held = self.items.get(entry["sha256"]) if is_entry(entry) else None
                if held is None:
                    notruns.append("input %s: needs the item of evidence entry %d, not held" % (name, idx))
                    continue
                if idx not in relied:
                    notruns.append("input %s: evidence entry %d is not relied on by step 2" % (name, idx))
                    continue
                if "pointer" not in src:
                    values[name] = sha256_hex(held[0])
                    continue
                if not isinstance(src["pointer"], str):
                    fails.append("input %s: pointer is not a string" % name)
                    continue
                try:
                    doc = parse_strict(held[0], integers_only=False)
                except NotJSON as e:
                    fails.append("input %s: item of entry %d is not JSON: %s" % (name, idx, e))
                    continue
                ok, val = resolve_pointer(doc, src["pointer"])
                if not ok:
                    fails.append("input %s: pointer %s does not resolve" % (name, src["pointer"]))
                    continue
                values[name] = val
            else:
                fails.append("input %s: binding of the wrong JSON type" % name)
        if fails:
            return FAIL, fails + notruns, body_read
        if notruns:
            return NOT_RUN, notruns, body_read
        kind, out = run_rule(rule, values)
        if kind != "ok":
            return FAIL, ["%s (%s)" % (out, "wrong JSON type" if kind == "type" else "rule inputs")], body_read
        if not json_equal(out, c["result"]):
            return FAIL, ["re-run gives %s, check.result is %s" % (json.dumps(out), json.dumps(c["result"]))], body_read
        return PASS, None, body_read


def check_case(record_bytes, items, upper_time_bound, policy, hold=()):
    """Full check of one record with the checker's own inputs. Returns the report."""
    rep = {"text": TEXT}
    prob = policy_problem(policy)
    try:
        rep["policy_sha256"] = sha256_hex(canonical(policy))
    except ValueError:
        rep["policy_sha256"] = None
    if prob:
        rep.update(state="no verdict", policy_invalid=prob, steps=None)
        return rep
    holdings = Holdings(hold)
    rep["held"] = holdings.describe()
    rep.update(Checker(policy, items, holdings).check(record_bytes, upper_time_bound))
    return rep


def summary_line(rep):
    """Section 4.4: names the state and every step's result."""
    s = rep.get("steps")
    if not s:
        return "state=%s; no step ran" % rep["state"]
    return "state=%s; step 1 %s; step 2 %s; step 3 %s" % (rep["state"], s["1"], s["2"], s["3"])
