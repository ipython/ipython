from IPython.core.tips import _tips

import importlib
import importlib.util
import os
import sys
import types
from datetime import datetime

import pytest

import IPython.core.tips as tips_mod

all_tips = _tips["random"] + list(_tips["every_year"].values())


@pytest.mark.skipif(os.name != "nt", reason="Windows console may crash with Unicode")
@pytest.mark.parametrize("tip", all_tips)
def test_tips(tip):
    assert tip.isascii()


def test_pick_tip_special_day(monkeypatch):
    monkeypatch.setattr(
        tips_mod, "datetime", types.SimpleNamespace(now=lambda: datetime(2025, 1, 1))
    )
    assert tips_mod.pick_tip() == "Happy new year!"


def test_pick_tip_random_day(monkeypatch):
    # a day with no every-year tip falls back to a random one
    assert (6, 15) not in tips_mod._tips["every_year"]
    monkeypatch.setattr(
        tips_mod, "datetime", types.SimpleNamespace(now=lambda: datetime(2025, 6, 15))
    )
    # pick_tip imports `choice` when it runs, so patch it in random
    monkeypatch.setattr("random.choice", lambda seq: seq[0])
    assert tips_mod.pick_tip() == tips_mod._tips["random"][0]


def test_tips_filtered_on_windows(monkeypatch):
    try:
        with monkeypatch.context() as m:
            m.setattr(os, "name", "nt")
            mod = importlib.reload(tips_mod)
            # non-ASCII every-year tips are filtered out on Windows
            assert all(tip.isascii() for tip in mod._tips["every_year"].values())
            assert (1, 1) in mod._tips["every_year"]
            # the (10, 11) anniversary tip contains a non-ASCII name
            assert (10, 11) not in mod._tips["every_year"]
            assert any("Windows" in tip for tip in mod._tips["random"])
    finally:
        importlib.reload(tips_mod)


def test_unicode_tips_on_non_windows():
    # on non-Windows platforms, unicode completion tips are included and
    # every-year tips are not filtered
    if os.name == "nt":
        pytest.skip("non-Windows only")
    assert (10, 11) in tips_mod._tips["every_year"]
    assert any("LaTeX" in tip for tip in tips_mod._tips["random"])


def test_argcomplete_tip_added_when_available(monkeypatch):
    # tips looks argcomplete up with find_spec rather than importing it, so
    # pretend the module is on sys.path without providing one
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "argcomplete":
            return types.SimpleNamespace(name=name)
        return real_find_spec(name, *args, **kwargs)

    try:
        with monkeypatch.context() as m:
            m.setattr(importlib.util, "find_spec", fake_find_spec)
            mod = importlib.reload(tips_mod)
            assert any("argcomplete" in tip for tip in mod._tips["random"])
    finally:
        importlib.reload(tips_mod)


def test_argcomplete_tip_absent_when_unavailable(monkeypatch):
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "argcomplete":
            return None
        return real_find_spec(name, *args, **kwargs)

    try:
        with monkeypatch.context() as m:
            m.setattr(importlib.util, "find_spec", fake_find_spec)
            mod = importlib.reload(tips_mod)
            assert not any("argcomplete" in tip for tip in mod._tips["random"])
    finally:
        importlib.reload(tips_mod)
