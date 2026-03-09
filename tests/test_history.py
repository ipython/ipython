# coding: utf-8
"""Tests for the IPython tab-completion machinery."""
# -----------------------------------------------------------------------------
# Module imports
# -----------------------------------------------------------------------------

# stdlib
import io
import gc
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from tempfile import TemporaryDirectory

# our own packages
from traitlets.config.loader import Config

from IPython.core.history import HistoryAccessor, HistoryManager, extract_hist_ranges

import pytest


def test_proper_default_encoding():
    assert sys.getdefaultencoding() == "utf-8"


def hmmax_instance_maker(N: int):
    if os.name == "nt":

        @pytest.fixture()
        def inner():
            pass

    else:

        @pytest.fixture()
        def inner():
            assert HistoryManager._max_inst == 1
            HistoryManager._max_inst = N
            lh = len(HistoryManager._instances)
            try:
                yield
                gc.collect()
                assert len(HistoryManager._instances) == lh
            finally:
                HistoryManager._max_inst = 1

    return inner


hmmax2 = hmmax_instance_maker(2)
hmmax3 = hmmax_instance_maker(3)


def test_history(hmmax2):
    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        hist_manager_ori = ip.history_manager
        hist_file = tmp_path / "history_test_history1.sqlite"
        try:
            ip.history_manager = HistoryManager(shell=ip, hist_file=hist_file)
            hist = ["a=1", "def f():\n    test = 1\n    return test", "b='€Æ¾÷ß'"]
            for i, h in enumerate(hist, start=1):
                ip.history_manager.store_inputs(i, h)

            ip.history_manager.db_log_output = True
            ip.history_manager.output_hist_reprs[3] = "spam"
            ip.history_manager.store_output(3)

            assert ip.history_manager.input_hist_raw == [""] + hist

            grs = ip.history_manager._get_range_session
            assert list(grs(start=2, stop=-1)) == list(zip([0], [2], hist[1:-1]))
            assert list(grs(start=-2)) == list(zip([0, 0], [2, 3], hist[-2:]))
            assert list(grs(output=True)) == list(
                zip([0, 0, 0], [1, 2, 3], zip(hist, [None, None, "spam"]))
            )

            ip.run_line_magic("hist", "2-500")

            ip.run_line_magic("hist", "-f %s" % (tmp_path / "test1"))
            ip.run_line_magic("hist", "-pf %s" % (tmp_path / "test2"))
            ip.run_line_magic("hist", "-nf %s" % (tmp_path / "test3"))
            ip.run_line_magic("save", "%s 1-10" % (tmp_path / "test4"))

            ip.history_manager.reset()
            newcmds = ["z=5", "class X(object):\n    pass", "k='p'", "z=5"]
            for i, cmd in enumerate(newcmds, start=1):
                ip.history_manager.store_inputs(i, cmd)
            gothist = ip.history_manager.get_range(start=1, stop=4)
            assert list(gothist) == list(zip([0, 0, 0], [1, 2, 3], newcmds))

            gothist = ip.history_manager.get_range(-1, 1, 4)
            assert list(gothist) == list(zip([1, 1, 1], [1, 2, 3], hist))

            newhist = [(2, i, c) for (i, c) in enumerate(newcmds, 1)]

            gothist = ip.history_manager.get_tail(5, output=True, include_latest=True)
            expected = [(1, 3, (hist[-1], "spam"))] + [
                (s, n, (c, None)) for (s, n, c) in newhist
            ]
            assert list(gothist) == expected

            gothist = ip.history_manager.get_tail(2)
            expected = newhist[-3:-1]
            assert list(gothist) == expected

            gothist = ip.history_manager.search("*test*")
            assert list(gothist) == [(1, 2, hist[1])]

            gothist = ip.history_manager.search("*=*")
            assert list(gothist) == [
                (1, 1, hist[0]),
                (1, 2, hist[1]),
                (1, 3, hist[2]),
                newhist[0],
                newhist[2],
                newhist[3],
            ]

            gothist = ip.history_manager.search("*=*", n=4)
            assert list(gothist) == [
                (1, 3, hist[2]),
                newhist[0],
                newhist[2],
                newhist[3],
            ]

            gothist = ip.history_manager.search("*=*", unique=True)
            assert list(gothist) == [
                (1, 1, hist[0]),
                (1, 2, hist[1]),
                (1, 3, hist[2]),
                newhist[2],
                newhist[3],
            ]

            gothist = ip.history_manager.search("*=*", unique=True, n=3)
            assert list(gothist) == [(1, 3, hist[2]), newhist[2], newhist[3]]

            gothist = ip.history_manager.search("b*", output=True)
            assert list(gothist) == [(1, 3, (hist[2], "spam"))]

        finally:
            ip.history_manager.end_session()
            ip.history_manager.save_thread.stop()
            ip.history_manager.db.close()
            ip.history_manager = hist_manager_ori


def test_extract_hist_ranges():
    instr = "1 2/3 ~4/5-6 ~4/7-~4/9 ~9/2-~7/5 ~10/"
    expected = [
        (0, 1, 2),
        (2, 3, 4),
        (-4, 5, 7),
        (-4, 7, 10),
        (-9, 2, None),
        (-8, 1, None),
        (-7, 1, 6),
        (-10, 1, None),
    ]
    actual = list(extract_hist_ranges(instr))
    assert actual == expected


def test_extract_hist_ranges_empty_str():
    instr = ""
    expected = [(0, 1, None)]
    actual = list(extract_hist_ranges(instr))
    assert actual == expected


def test_magic_rerun():
    ip = get_ipython()
    ip.run_cell("a = 10", store_history=True)
    ip.run_cell("a += 1", store_history=True)
    assert ip.user_ns["a"] == 11
    ip.run_cell("%rerun", store_history=True)
    assert ip.user_ns["a"] == 12


def test_timestamp_type():
    ip = get_ipython()
    info = ip.history_manager.get_session_info()
    assert isinstance(info[1], datetime)


def test_hist_file_config(hmmax3):
    cfg = Config()
    tfile = tempfile.NamedTemporaryFile(delete=False)
    cfg.HistoryManager.hist_file = Path(tfile.name)
    hm = None
    try:
        hm = HistoryManager(shell=get_ipython(), config=cfg)
        assert hm.hist_file == cfg.HistoryManager.hist_file
    finally:
        try:
            if hm is not None:
                hm.end_session()
                hm.save_thread.stop()
                hm.db.close()
        except Exception:
            pass

        try:
            Path(tfile.name).unlink()
        except OSError:
            pass