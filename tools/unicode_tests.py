#!/usr/bin/env python
# coding: utf-8
"""These tests have to be run separately from the main test suite (iptest),
because that sets the default encoding to utf-8, and it cannot be changed after
the interpreter is up and running. The default encoding in a Python 2.x 
environment is ASCII."""
import unittest
import sys, os.path

from IPython.core import ipapi
from IPython.core import compilerop
from IPython.core.history import HistoryManager
from IPython.utils.tempdir import TemporaryDirectory

assert sys.getdefaultencoding() == "ascii"

class CompileropTest(unittest.TestCase):
    def test_accept_unicode(self):
        cp = compilerop.CachingCompiler()
        cp(u"t = 'žćčšđ'", "single")
        
class HistoryTest(unittest.TestCase):
    def test_reload_unicode(self):
        ip = ipapi.get()
        with TemporaryDirectory() as tmpdir:
            histfile = os.path.realpath(os.path.join(tmpdir, 'history.json'))
            # Ensure that we restore the history management that we mess with in
            # this test doesn't affect the IPython instance used by the test suite
            # beyond this test.
            hist_manager_ori = ip.history_manager
            try:
                ip.history_manager = HistoryManager(ip)
                ip.history_manager.hist_file = histfile
                print 'test',histfile
                hist = [u"t = 'žćčšđ'"]
                # test save and load
                ip.history_manager.input_hist_raw[:] = []
                for h in hist:
                    ip.history_manager.input_hist_raw.append(h)
                ip.save_history()
                ip.history_manager.input_hist_raw[:] = []
                ip.reload_history()
                self.assert_equal(len(ip.history_manager.input_hist_raw), len(hist))
                for i,h in enumerate(hist):
                    nt.assert_equal(hist[i], ip.history_manager.input_hist_raw[i])
            finally:
                # Restore history manager
                ip.history_manager = hist_manager_ori

if __name__ == "__main__":
    unittest.main()
