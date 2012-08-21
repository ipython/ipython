#-----------------------------------------------------------------------------
# Copyright (C) 2012 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import os
import unittest
import base64

from IPython.zmq.kernelmanager import KernelManager
from IPython.frontend.terminal.console.interactiveshell \
    import ZMQTerminalInteractiveShell
from IPython.utils.tempdir import NamedFileInTemporaryDirectory
from IPython.testing.tools import monkeypatch
from IPython.testing.decorators import skip_without
from IPython.utils.ipstruct import Struct
from IPython.utils.process import find_cmd


SCRIPT_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'writetofile.py')


class ZMQTerminalInteractiveShellTestCase(unittest.TestCase):

    def setUp(self):
        km = KernelManager()
        self.shell = ZMQTerminalInteractiveShell(kernel_manager=km)
        self.raw = b'dummy data'
        self.mime = 'image/png'
        self.data = {self.mime: base64.encodestring(self.raw)}

    def test_no_call_by_default(self):
        def raise_if_called(*args, **kwds):
            assert False

        shell = self.shell
        shell.handle_image_PIL
        shell.handle_image_stream
        shell.handle_image_tempfile
        shell.handle_image_callable

        shell.handle_image(None, None)  # arguments are dummy

    @skip_without('PIL')
    def test_handle_image_PIL(self):
        import PIL.Image

        open_called_with = []
        show_called_with = []

        def fake_open(arg):
            open_called_with.append(arg)
            return Struct(show=lambda: show_called_with.append(None))

        with monkeypatch(PIL.Image, 'open', fake_open):
            self.shell.handle_image_PIL(self.data, self.mime)

        assert len(open_called_with) == 1
        assert len(show_called_with) == 1
        assert open_called_with[0].getvalue() == self.raw

    @staticmethod
    def get_handler_command(inpath, outpath):
        return [find_cmd('python'), SCRIPT_PATH, inpath, outpath]

    def check_handler_with_file(self, inpath, handler):
        shell = self.shell
        configname = '{0}_image_handler'.format(handler)
        funcname = 'handle_image_{0}'.format(handler)

        assert hasattr(shell, configname)
        assert hasattr(shell, funcname)

        with NamedFileInTemporaryDirectory('data') as file:
            cmd = self.get_handler_command(inpath, file.name)
            setattr(shell, configname, cmd)
            getattr(shell, funcname)(self.data, self.mime)
            transferred = file.read()

        assert transferred == self.raw

    def test_handle_image_stream(self):
        self.check_handler_with_file('-', 'stream')

    def test_handle_image_tempfile(self):
        self.check_handler_with_file('{file}', 'tempfile')

    def test_handle_image_callable(self):
        called_with = []
        self.shell.callable_image_handler = called_with.append
        self.shell.handle_image_callable(self.data, self.mime)
        assert len(called_with) == 1
        assert called_with[0] is self.data
