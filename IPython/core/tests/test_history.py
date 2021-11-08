# coding: utf-8
"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import io
from pathlib import Path
import sys
import tempfile
from datetime import datetime
import sqlite3

# our own packages
from traitlets.config.loader import Config
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core.history import HistoryManager, extract_hist_ranges
from IPython.testing.decorators import skipif
from IPython.utils.capture import capture_output

def test_proper_default_encoding():
    assert sys.getdefaultencoding() == "utf-8"

@skipif(sqlite3.sqlite_version_info > (3,24,0))
def test_history():
    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        hist_manager_ori = ip.history_manager
        hist_file = tmp_path / "history.sqlite"
        try:
            ip.history_manager = HistoryManager(shell=ip, hist_file=hist_file)
            hist = ["a=1", "def f():\n    test = 1\n    return test", "b='€Æ¾÷ß'"]
            for i, h in enumerate(hist, start=1):
                ip.history_manager.store_inputs(i, h)

            ip.history_manager.db_log_output = True
            # Doesn't match the input, but we'll just check it's stored.
            ip.history_manager.output_hist_reprs[3] = "spam"
            ip.history_manager.store_output(3)

            assert ip.history_manager.input_hist_raw == [""] + hist

            # Detailed tests for _get_range_session
            grs = ip.history_manager._get_range_session
            assert list(grs(start=2, stop=-1)) == list(zip([0], [2], hist[1:-1]))
            assert list(grs(start=-2)) == list(zip([0, 0], [2, 3], hist[-2:]))
            assert list(grs(output=True)) == list(
                zip([0, 0, 0], [1, 2, 3], zip(hist, [None, None, "spam"]))
            )

            # Check whether specifying a range beyond the end of the current
            # session results in an error (gh-804)
            ip.magic('%hist 2-500')

            # Check that we can write non-ascii characters to a file
            ip.magic("%%hist -f %s" % (tmp_path / "test1"))
            ip.magic("%%hist -pf %s" % (tmp_path / "test2"))
            ip.magic("%%hist -nf %s" % (tmp_path / "test3"))
            ip.magic("%%save %s 1-10" % (tmp_path / "test4"))

            # New session
            ip.history_manager.reset()
            newcmds = ["z=5", "class X(object):\n    pass", "k='p'", "z=5"]
            for i, cmd in enumerate(newcmds, start=1):
                ip.history_manager.store_inputs(i, cmd)
            gothist = ip.history_manager.get_range(start=1, stop=4)
            assert list(gothist) == list(zip([0, 0, 0], [1, 2, 3], newcmds))
            # Previous session:
            gothist = ip.history_manager.get_range(-1, 1, 4)
            assert list(gothist) == list(zip([1, 1, 1], [1, 2, 3], hist))

            newhist = [(2, i, c) for (i, c) in enumerate(newcmds, 1)]

            # Check get_hist_tail
            gothist = ip.history_manager.get_tail(5, output=True,
                                                    include_latest=True)
            expected = [(1, 3, (hist[-1], "spam"))] \
                + [(s, n, (c, None)) for (s, n, c) in newhist]
            assert list(gothist) == expected

            gothist = ip.history_manager.get_tail(2)
            expected = newhist[-3:-1]
            assert list(gothist) == expected

            # Check get_hist_search

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

            # Cross testing: check that magic %save can get previous session.
            testfilename = (tmp_path / "test.py").resolve()
            ip.magic("save " + str(testfilename) + " ~1/1-3")
            with io.open(testfilename, encoding="utf-8") as testfile:
                assert testfile.read() == "# coding: utf-8\n" + "\n".join(hist) + "\n"

            # Duplicate line numbers - check that it doesn't crash, and
            # gets a new session
            ip.history_manager.store_inputs(1, "rogue")
            ip.history_manager.writeout_cache()
            assert ip.history_manager.session_number == 3
        finally:
            # Ensure saving thread is shut down before we try to clean up the files
            ip.history_manager.save_thread.stop()
            # Forcibly close database rather than relying on garbage collection
            ip.history_manager.db.close()
            # Restore history manager
            ip.history_manager = hist_manager_ori


def test_extract_hist_ranges():
    instr = "1 2/3 ~4/5-6 ~4/7-~4/9 ~9/2-~7/5 ~10/"
    expected = [(0, 1, 2),  # 0 == current session
                (2, 3, 4),
                (-4, 5, 7),
                (-4, 7, 10),
                (-9, 2, None),  # None == to end
                (-8, 1, None),
                (-7, 1, 6),
                (-10, 1, None)]
    actual = list(extract_hist_ranges(instr))
    assert actual == expected


def test_extract_hist_ranges_empty_str():
    instr = ""
    expected = [(0, 1, None)]  # 0 == current session, None == to end
    actual = list(extract_hist_ranges(instr))
    assert actual == expected


def test_magic_rerun():
    """Simple test for %rerun (no args -> rerun last line)"""
    ip = get_ipython()
    ip.run_cell("a = 10", store_history=True)
    ip.run_cell("a += 1", store_history=True)
    assert ip.user_ns["a"] == 11
    ip.run_cell("%rerun", store_history=True)
    assert ip.user_ns["a"] == 12

def test_magic_rerun_search():
    """Test for %rerun -g (searching for text match)"""
    ip = get_ipython()
    ip.run_cell("a = 10", store_history=True)
    ip.run_cell("a += 1", store_history=True)
    nt.assert_equal(ip.user_ns["a"], 11)
    ip.run_cell("%rerun -g 10", store_history=True)
    nt.assert_equal(ip.user_ns["a"], 10)


def test_magic_rerun_quiet():
    """Simple test for %rerun -q (quiet, no echoing of output)"""
    ip = get_ipython()
    ip.run_cell("a = 10", store_history=True)
    ip.run_cell("a += 1", store_history=True)
    nt.assert_equal(ip.user_ns["a"], 11)
    with capture_output() as cap:
        ip.run_cell("%rerun -q", store_history=True)
    nt.assert_equal(ip.user_ns["a"], 12)
    nt.assert_not_in("a += 1", cap.stdout)


def test_timestamp_type():
    ip = get_ipython()
    info = ip.history_manager.get_session_info()
    assert isinstance(info[1], datetime)

def test_hist_file_config():
    cfg = Config()
    tfile = tempfile.NamedTemporaryFile(delete=False)
    cfg.HistoryManager.hist_file = Path(tfile.name)
    try:
        hm = HistoryManager(shell=get_ipython(), config=cfg)
        assert hm.hist_file == cfg.HistoryManager.hist_file
    finally:
        try:
            Path(tfile.name).unlink()
        except OSError:
            # same catch as in testing.tools.TempFileMixin
            # On Windows, even though we close the file, we still can't
            # delete it.  I have no clue why
            pass

def test_histmanager_disabled():
    """Ensure that disabling the history manager doesn't create a database."""
    cfg = Config()
    cfg.HistoryAccessor.enabled = False

    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        hist_manager_ori = ip.history_manager
        hist_file = Path(tmpdir) / "history.sqlite"
        cfg.HistoryManager.hist_file = hist_file
        try:
            ip.history_manager = HistoryManager(shell=ip, config=cfg)
            hist = ["a=1", "def f():\n    test = 1\n    return test", "b='€Æ¾÷ß'"]
            for i, h in enumerate(hist, start=1):
                ip.history_manager.store_inputs(i, h)
            assert ip.history_manager.input_hist_raw == [""] + hist
            ip.history_manager.reset()
            ip.history_manager.end_session()
        finally:
            ip.history_manager = hist_manager_ori

    # hist_file should not be created
    assert hist_file.exists() is False
