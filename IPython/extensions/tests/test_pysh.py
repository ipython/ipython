import nose.tools as nt
from IPython.core.splitinput import LineInfo
from IPython.extensions.pysh import (
    unload_ipython_extension, load_ipython_extension)


from IPython.testing.globalipapp import get_ipython

ip = get_ipython()


class TestPySh(object):

    def setup(self):
        ip.magic("alias ls ls")
        ip.magic("alias from from")
        ip.magic("alias apt-get apt-get")
        self.checker, self.handler = load_ipython_extension(ip)
        self.pfm = ip.prefilter_manager

    def teardown(self):
        unload_ipython_extension(ip)

    def test_unload_inverts_load(self):
        unload_ipython_extension(ip)
        nt.assert_false(
            self.handler.handler_name in self.pfm.handlers,
            'oops, unload did not remove the pysh handler')
        nt.assert_false(
            self.checker in self.pfm.checkers,
            'oops, unload did not remove the pysh checker')

    def test_handler_basic(self):
        expected = "get_ipython().system('ls')"
        actual = self.handler.handle(LineInfo("ls"))
        nt.assert_equal(actual, expected)

    def test_handler_doesnt_split_dash(self):
        expected = "get_ipython().system('apt-get install foo')"
        actual = self.handler.handle(LineInfo("apt-get install foo"))
        nt.assert_equal(actual, expected)

    def test_checker_nil(self):
        err = 'pysh checker should ignore blank lines'
        nt.assert_equal(self.checker.check(LineInfo("")), None, err)
        nt.assert_equal(self.checker.check(LineInfo(" ")), None, err)

    def test_checker_magic(self):
        err = 'pysh checker should not trigger on magic'
        nt.assert_equal(self.checker.check(LineInfo("%magic")), None, err)

    def test_checker_reserved(self):
        err = "'ed' is reserved for ipython, system cmd should be ignored"
        actual = self.checker.check(LineInfo("ed"))
        nt.assert_equal(actual, None, err)
        err = "'from' is reserved for ipython, system cmd should be ignored"
        actual = self.checker.check(LineInfo("from"))
        nt.assert_equal(actual, None, err)

    def test_checker_special_cases(self):
        err = 'pysh checker should trigger on each of "~/."'
        actual = self.checker.check(LineInfo("~/bin/foo"))
        nt.assert_equal(actual, self.handler, err)
        actual = self.checker.check(LineInfo("/bar"))
        nt.assert_equal(actual, self.handler, err)
        actual = self.checker.check(LineInfo("./foo-bar"))
        nt.assert_equal(actual, self.handler, err)

    def test_checker_registered_cmd_alias(self):
        err = 'pysh should trigger on registered cmd alias'
        nt.assert_equal(self.checker.check(LineInfo("ls")), self.handler)
        err = 'pysh should NOT trigger on unregistered cmd alias'
        nt.assert_equal(self.checker.check(LineInfo("which")), None, err)
