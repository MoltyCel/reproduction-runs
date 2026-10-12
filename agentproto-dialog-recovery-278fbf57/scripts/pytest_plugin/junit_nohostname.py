"""pytest plugin for this run, loaded with `-p junit_nohostname` on every pytest call.

pytest's JUnit XML writer stores `hostname=platform.node()` in the <testsuite>
element. The machine name of the computer this run was made on carries a
personal name, and macOS lets only root change it. This plugin replaces the
`platform` name inside `_pytest.junitxml` only (not the global `platform`
module), so the attribute reads "localhost". Nothing else in pytest, in the
tests or in the package under test sees a different value. No repo code is
imported or touched.
"""
import platform as _platform
import types

import _pytest.junitxml as _junitxml

_junitxml.platform = types.SimpleNamespace(
    **{k: getattr(_platform, k) for k in dir(_platform) if not k.startswith("__")},
)
_junitxml.platform.node = lambda: "localhost"
