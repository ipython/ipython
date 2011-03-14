"""Tests for the IPython tab-completion machinery.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import os
import sys
import unittest

# third party
import nose.tools as nt

# our own packages
from IPython.utils.tempdir import TemporaryDirectory
from IPython.core.history import HistoryManager, extract_hist_ranges

def test_history():

    ip = get_ipython()
    with TemporaryDirectory() as tmpdir:
        #tmpdir = '/software/temp'
        histfile = os.path.realpath(os.path.join(tmpdir, 'history.sqlite'))
        # Ensure that we restore the history management that we mess with in
        # this test doesn't affect the IPython instance used by the test suite
        # beyond this test.
        hist_manager_ori = ip.history_manager
        try:
            ip.history_manager = HistoryManager(shell=ip)
            ip.history_manager.hist_file = histfile
            ip.history_manager.init_db()  # Has to be called after changing file
            ip.history_manager.reset()
            print 'test',histfile
            hist = ['a=1', 'def f():\n    test = 1\n    return test', 'b=2']
            for i, h in enumerate(hist, start=1):
                ip.history_manager.store_inputs(i, h)
            
            ip.history_manager.db_log_output = True
            # Doesn't match the input, but we'll just check it's stored.
            ip.history_manager.output_hist[3].append("spam")
            ip.history_manager.store_output(3)
            
            nt.assert_equal(ip.history_manager.input_hist_raw, [''] + hist)
            
            # Check lines were written to DB
            c = ip.history_manager.db.execute("SELECT source_raw FROM history")
            nt.assert_equal([x for x, in c], hist)
              
            # New session
            ip.history_manager.reset()
            newcmds = ["z=5","class X(object):\n    pass", "k='p'"]
            for i, cmd in enumerate(newcmds, start=1):
                ip.history_manager.store_inputs(i, cmd)
            gothist = ip.history_manager.get_history(start=1, stop=4)
            nt.assert_equal(list(gothist), zip([0,0,0],[1,2,3], newcmds))
            # Previous session:
            gothist = ip.history_manager.get_history(-1, 1, 4)
            nt.assert_equal(list(gothist), zip([1,1,1],[1,2,3], hist))
            
            # Check get_hist_tail
            gothist = ip.history_manager.get_hist_tail(4, output=True)
            expected = [(1, 3, (hist[-1], [repr("spam")])),
                        (2, 1, (newcmds[0], None)),
                        (2, 2, (newcmds[1], None)),
                        (2, 3, (newcmds[2], None)),]
            nt.assert_equal(list(gothist), expected)
            
            # Check get_hist_search
            gothist = ip.history_manager.get_hist_search("*test*")
            nt.assert_equal(list(gothist), [(1,2,hist[1])] )
            gothist = ip.history_manager.get_hist_search("b*", output=True)
            nt.assert_equal(list(gothist), [(1,3,(hist[2],[repr("spam")]))] )
            
            # Cross testing: check that magic %save can get previous session.
            testfilename = os.path.realpath(os.path.join(tmpdir, "test.py"))
            ip.magic_save(testfilename + " ~1/1-3")
            testfile = open(testfilename, "r")
            nt.assert_equal(testfile.read(), "\n".join(hist))
        finally:
            # Restore history manager
            ip.history_manager = hist_manager_ori

def test_extract_hist_ranges():
    instr = "1 2/3 ~4/5-6 ~4/7-~4/9 ~9/2-~7/5"
    expected = [(0, 1, 2),  # 0 == current session
                (2, 3, 4),
                (-4, 5, 7),
                (-4, 7, 10),
                (-9, 2, None),  # None == to end
                (-8, 1, None),
                (-7, 1, 6)]
    actual = list(extract_hist_ranges(instr))
    nt.assert_equal(actual, expected)
