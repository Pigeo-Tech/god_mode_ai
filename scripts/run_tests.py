"""Stdlib test runner (used when pytest is unavailable offline).

Installs a minimal `pytest` shim (raises/mark/fixture), imports every
backend/tests/unit/test_*.py module, and runs each test_* function — sync directly, async via
asyncio.run — mirroring pytest-asyncio auto mode. Optional argv filters by substring.
"""
import asyncio
import importlib
import inspect
import pathlib
import sys
import traceback
import types
from contextlib import contextmanager

pytest = types.ModuleType("pytest")

@contextmanager
def _raises(exc_type):
    raised = None
    try:
        yield
    except exc_type as e:
        raised = e
    if raised is None:
        raise AssertionError(f"DID NOT RAISE {exc_type.__name__}")

pytest.raises = _raises
pytest.mark = types.SimpleNamespace(asyncio=lambda f: f)
pytest.fixture = lambda *a, **k: (lambda f: f)
sys.modules["pytest"] = pytest

sys.path.insert(0, ".")
flt = sys.argv[1] if len(sys.argv) > 1 else ""

mod_paths = sorted(pathlib.Path("backend/tests/unit").glob("test_*.py"))
passed = failed = 0
failures = []
for path in mod_paths:
    mod_name = ".".join(path.with_suffix("").parts)
    mod = importlib.import_module(mod_name)
    for name in sorted(dir(mod)):
        if not name.startswith("test_") or flt not in name:
            continue
        fn = getattr(mod, name)
        if not callable(fn):
            continue
        try:
            asyncio.run(fn()) if inspect.iscoroutinefunction(fn) else fn()
            passed += 1
            print(f"PASS {mod_name}::{name}")
        except Exception:
            failed += 1
            failures.append((f"{mod_name}::{name}", traceback.format_exc()))
            print(f"FAIL {mod_name}::{name}")

print(f"\n==== {passed} passed, {failed} failed ====")
for name, tb in failures:
    print(f"\n--- {name} ---\n{tb}")
sys.exit(1 if failed else 0)
