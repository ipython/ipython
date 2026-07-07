"""Tests for small IPython.utils modules: data, timing, frame and encoding."""

import importlib
import sys
import time
import types

import pytest

from IPython.utils import data as data_mod
from IPython.utils import encoding as encoding_mod
from IPython.utils import frame as frame_mod
from IPython.utils import timing as timing_mod

# -----------------------------------------------------------------------------
# IPython.utils.data
# -----------------------------------------------------------------------------


def test_uniq_stable_is_deprecated():
    with pytest.deprecated_call():
        result = data_mod.uniq_stable([1, 2, 1, 3, 2, 4])
    assert result == [1, 2, 3, 4]


def test_uniq_stable_accepts_iterables():
    with pytest.deprecated_call():
        result = data_mod.uniq_stable(iter("abracadabra"))
    assert result == ["a", "b", "r", "c", "d"]


def test_chop():
    assert data_mod.chop("abcdefg", 3) == ["abc", "def", "g"]
    assert data_mod.chop(list(range(4)), 2) == [[0, 1], [2, 3]]
    assert data_mod.chop([], 3) == []
    assert data_mod.chop((1, 2, 3), 5) == [(1, 2, 3)]


# -----------------------------------------------------------------------------
# IPython.utils.timing
# -----------------------------------------------------------------------------


def test_clock_functions():
    user = timing_mod.clocku()
    system = timing_mod.clocks()
    total = timing_mod.clock()
    for value in (user, system, total):
        assert isinstance(value, float)
        assert value >= 0.0
    # total user+system time measured later must be at least the user
    # time measured earlier
    assert total >= user

    user2, system2 = timing_mod.clock2()
    assert user2 >= user
    assert system2 >= system


def test_timings_out_single_rep():
    calls = []

    def add(a, b=0):
        calls.append((a, b))
        return a + b

    tot, per_call, out = timing_mod.timings_out(1, add, 2, b=3)
    assert out == 5
    assert calls == [(2, 3)]
    assert per_call == tot


def test_timings_out_multiple_reps():
    calls = []

    def add(a, b=0):
        calls.append((a, b))
        return a + b

    tot, per_call, out = timing_mod.timings_out(4, add, 1, b=1)
    assert out == 2
    assert len(calls) == 4
    assert per_call == pytest.approx(tot / 4)


def test_timings_out_rejects_bad_reps():
    with pytest.raises(AssertionError, match="reps must be >= 1"):
        timing_mod.timings_out(0, lambda: None)


def test_timings():
    tot, per_call = timing_mod.timings(2, lambda: None)
    assert tot >= 0.0
    assert per_call == pytest.approx(tot / 2)


def test_timing():
    result = []
    tot = timing_mod.timing(result.append, "x")
    assert tot >= 0.0
    assert result == ["x"]


def _reload_timing():
    return importlib.reload(timing_mod)


def test_timing_without_getrusage(monkeypatch):
    # simulate platforms (e.g. jupyterlite) where the resource module exists
    # but has no getrusage
    try:
        with monkeypatch.context() as m:
            m.setitem(sys.modules, "resource", types.ModuleType("resource"))
            mod = _reload_timing()
            assert mod.clocku is time.process_time
            assert mod.clocks is time.process_time
            assert mod.clock is time.process_time
            user, system = mod.clock2()
            assert user >= 0.0
            assert system == 0.0
    finally:
        _reload_timing()


def test_timing_without_resource_module(monkeypatch):
    # simulate platforms (e.g. Windows) with no resource module at all
    class BlockResource:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "resource":
                raise ModuleNotFoundError("No module named 'resource'")
            return None

    try:
        with monkeypatch.context() as m:
            m.delitem(sys.modules, "resource", raising=False)
            m.setattr(sys, "meta_path", [BlockResource()] + sys.meta_path)
            mod = _reload_timing()
            assert mod.resource is None
            assert mod.clock is time.process_time
            assert mod.clock2()[1] == 0.0
    finally:
        _reload_timing()


# -----------------------------------------------------------------------------
# IPython.utils.frame
# -----------------------------------------------------------------------------


def test_extract_module_locals():
    sentinel = "local-value"
    module, local_ns = frame_mod.extract_module_locals(0)
    assert module is sys.modules[__name__]
    assert local_ns["sentinel"] == sentinel


def test_extract_module_locals_depth():
    def inner():
        hidden = "inner-only"  # noqa: F841
        return frame_mod.extract_module_locals(1)

    outer_var = "outer-value"
    module, local_ns = inner()
    assert module is sys.modules[__name__]
    # depth=1 skips inner()'s frame and returns this function's locals
    assert local_ns["outer_var"] == outer_var
    assert "hidden" not in local_ns


# -----------------------------------------------------------------------------
# IPython.utils.encoding
# -----------------------------------------------------------------------------


class FakeStream:
    def __init__(self, enc):
        self.encoding = enc


def test_get_stream_enc():
    # no encoding attribute at all
    assert encoding_mod.get_stream_enc(object()) is None
    assert encoding_mod.get_stream_enc(object(), "default") == "default"
    # falsy encoding attribute
    assert encoding_mod.get_stream_enc(FakeStream(None), "default") == "default"
    assert encoding_mod.get_stream_enc(FakeStream(""), "default") == "default"
    # real encoding wins over the default
    assert encoding_mod.get_stream_enc(FakeStream("latin-1")) == "latin-1"
    assert encoding_mod.get_stream_enc(FakeStream("latin-1"), "utf-8") == "latin-1"


def test_getdefaultencoding_from_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStream("utf-8"))
    assert encoding_mod.getdefaultencoding() == "utf-8"


def test_getdefaultencoding_prefers_locale_over_ascii(monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStream("ascii"))
    monkeypatch.setattr(
        encoding_mod.locale, "getpreferredencoding", lambda: "latin-1"
    )
    assert encoding_mod.getdefaultencoding() == "latin-1"


def test_getdefaultencoding_locale_error(monkeypatch):
    # if getpreferredencoding raises, keep the stream encoding
    def boom():
        raise RuntimeError("no locale")

    monkeypatch.setattr(sys, "stdin", FakeStream("ascii"))
    monkeypatch.setattr(encoding_mod.locale, "getpreferredencoding", boom)
    assert encoding_mod.getdefaultencoding() == "ascii"


def test_getdefaultencoding_falls_back_to_sys(monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStream(None))
    monkeypatch.setattr(encoding_mod.locale, "getpreferredencoding", lambda: "")
    assert encoding_mod.getdefaultencoding() == sys.getdefaultencoding()


def test_getdefaultencoding_cp0(monkeypatch):
    # cp0 is an invalid Windows code page and is replaced by cp1252
    monkeypatch.setattr(sys, "stdin", FakeStream("cp0"))
    with pytest.warns(RuntimeWarning, match="cp0"):
        assert encoding_mod.getdefaultencoding() == "cp1252"


def test_getdefaultencoding_prefer_stream_deprecated(monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStream("utf-8"))
    with pytest.deprecated_call():
        assert encoding_mod.getdefaultencoding(True) == "utf-8"
    # even a falsy value triggers the deprecation path and forces
    # prefer_stream back to True
    with pytest.deprecated_call():
        assert encoding_mod.getdefaultencoding(False) == "utf-8"


def test_default_encoding_constant():
    import codecs

    assert isinstance(encoding_mod.DEFAULT_ENCODING, str)
    # must name a real codec
    assert codecs.lookup(encoding_mod.DEFAULT_ENCODING)
