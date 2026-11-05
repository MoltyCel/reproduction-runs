"""RFC 8785 JSON Canonicalization Scheme, written from RFC 8785 for these runs.

Scope: objects, arrays, strings, true/false/null and integers that are exactly
representable as IEEE 754 doubles (|n| <= 2**53). Non-integer numbers raise, because
ECMAScript Number serialisation (RFC 8785 section 3.2.2.3) is not implemented here.
Object members are sorted by the UTF-16 code units of their names (section 3.2.3).
Strings are serialised as ECMAScript JSON.stringify does (section 3.2.2.2).
"""


def _utf16_key(s):
    b = s.encode("utf-16-be", "surrogatepass")
    return [int.from_bytes(b[i:i + 2], "big") for i in range(0, len(b), 2)]


_ESC = {0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r", 0x22: '\\"', 0x5C: "\\\\"}


def _str(s):
    out = ['"']
    for ch in s:
        c = ord(ch)
        if c in _ESC:
            out.append(_ESC[c])
        elif c < 0x20:
            out.append("\\u%04x" % c)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def canonicalize(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        if abs(v) > 2 ** 53:
            raise ValueError("integer outside the exactly representable range")
        return str(v)
    if isinstance(v, float):
        raise ValueError("non-integer numbers are outside this implementation")
    if isinstance(v, str):
        return _str(v)
    if isinstance(v, list):
        return "[" + ",".join(canonicalize(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v, key=_utf16_key)
        return "{" + ",".join(_str(k) + ":" + canonicalize(v[k]) for k in keys) + "}"
    raise TypeError(type(v).__name__)


def jcs_bytes(v):
    return canonicalize(v).encode("utf-8")
