#!/usr/bin/env python
"""A few unit tests for the Shell module.
"""

from unittest import TestCase, main

from IPython import Shell

try:
    import matplotlib
    has_matplotlib = True
except ImportError:
    has_matplotlib = False

class ShellTestBase(TestCase):
    def _test(self,argv,ans):
        shell = Shell._select_shell(argv)
        err = 'Got %s != %s' % (shell,ans)
        self.failUnlessEqual(shell,ans,err)

class ArgsTestCase(ShellTestBase):
    def test_plain(self):
        self._test([],Shell.IPShell)

    def test_tkthread(self):
        self._test(['-tkthread'],Shell.IPShell)

    def test_gthread(self):
        self._test(['-gthread'],Shell.IPShellGTK)

    def test_qthread(self):
        self._test(['-qthread'],Shell.IPShellQt)

    def test_q4thread(self):
        self._test(['-q4thread'],Shell.IPShellQt4)

    def test_wthread(self):
        self._test(['-wthread'],Shell.IPShellWX)

if has_matplotlib:
    class MplArgsTestCase(ShellTestBase):
        def setUp(self):
            self.backend = matplotlib.rcParams['backend']

        def tearDown(self):
            matplotlib.rcParams['backend'] = self.backend

        def _test(self,argv,ans):
            shell = Shell._select_shell(argv)
            err = 'Got %s != %s' % (shell,ans)
            self.failUnlessEqual(shell,ans,err)

        def test_tk(self):
            matplotlib.rcParams['backend'] = 'TkAgg'
            self._test(['-pylab'],Shell.IPShellMatplotlib)

        def test_ps(self):
            matplotlib.rcParams['backend'] = 'PS'
            self._test(['-pylab'],Shell.IPShellMatplotlib)

        def test_gtk(self):
            matplotlib.rcParams['backend'] = 'GTKAgg'
            self._test(['-pylab'],Shell.IPShellMatplotlibGTK)

        def test_gtk_2(self):
            self._test(['-gthread','-pylab'],Shell.IPShellMatplotlibGTK)
            self.failUnlessEqual(matplotlib.rcParams['backend'],'GTKAgg')
            
        def test_qt(self):
            matplotlib.rcParams['backend'] = 'QtAgg'
            self._test(['-pylab'],Shell.IPShellMatplotlibQt)
            
        def test_qt_2(self):
            self._test(['-qthread','-pylab'],Shell.IPShellMatplotlibQt)
            self.failUnlessEqual(matplotlib.rcParams['backend'],'QtAgg')
            
        def test_qt4(self):
            matplotlib.rcParams['backend'] = 'Qt4Agg'
            self._test(['-pylab'],Shell.IPShellMatplotlibQt4)

        def test_qt4_2(self):
            self._test(['-q4thread','-pylab'],Shell.IPShellMatplotlibQt4)
            self.failUnlessEqual(matplotlib.rcParams['backend'],'Qt4Agg')
            
        def test_wx(self):
            matplotlib.rcParams['backend'] = 'WxAgg'
            self._test(['-pylab'],Shell.IPShellMatplotlibWX)
            
        def test_wx_2(self):
            self._test(['-pylab','-wthread'],Shell.IPShellMatplotlibWX)
            self.failUnlessEqual(matplotlib.rcParams['backend'],'WXAgg')
            

main()
