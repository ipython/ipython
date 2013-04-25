#-----------------------------------------------------------------------------
# Copyright (C) 2012 The IPython Development Team
#
# Distributed under the terms of the BSD License. The full license is in
# the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import os
import sys
import unittest
import base64

from IPython.kernel import KernelClient
from IPython.frontend.terminal.console.interactiveshell \
    import ZMQTerminalInteractiveShell
from IPython.utils.tempdir import TemporaryDirectory
from IPython.testing.tools import monkeypatch
from IPython.testing.decorators import skip_without
from IPython.utils.ipstruct import Struct


SCRIPT_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'writetofile.py')


class ZMQTerminalInteractiveShellTestCase(unittest.TestCase):

    def setUp(self):
        client = KernelClient()
        self.shell = ZMQTerminalInteractiveShell(kernel_client=client)
        self.raw = b'dummy data'
        self.mime = 'image/png'
        self.data = {self.mime: base64.encodestring(self.raw).decode('ascii')}

    def test_no_call_by_default(self):
        def raise_if_called(*args, **kwds):
            assert False

        shell = self.shell
        shell.handle_image_PIL = raise_if_called
        shell.handle_image_stream = raise_if_called
        shell.handle_image_tempfile = raise_if_called
        shell.handle_image_callable = raise_if_called

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

        self.assertEqual(len(open_called_with), 1)
        self.assertEqual(len(show_called_with), 1)
        self.assertEqual(open_called_with[0].getvalue(), self.raw)

    def check_handler_with_file(self, inpath, handler):
        shell = self.shell
        configname = '{0}_image_handler'.format(handler)
        funcname = 'handle_image_{0}'.format(handler)

        assert hasattr(shell, configname)
        assert hasattr(shell, funcname)

        with TemporaryDirectory() as tmpdir:
            outpath = os.path.join(tmpdir, 'data')
            cmd = [sys.executable, SCRIPT_PATH, inpath, outpath]
            setattr(shell, configname, cmd)
            getattr(shell, funcname)(self.data, self.mime)
            # cmd is called and file is closed.  So it's safe to open now.
            with open(outpath, 'rb') as file:
                transferred = file.read()

        self.assertEqual(transferred, self.raw)

    def test_handle_image_stream(self):
        self.check_handler_with_file('-', 'stream')

    def test_handle_image_tempfile(self):
        self.check_handler_with_file('{file}', 'tempfile')

    def test_handle_image_callable(self):
        called_with = []
        self.shell.callable_image_handler = called_with.append
        self.shell.handle_image_callable(self.data, self.mime)
        self.assertEqual(len(called_with), 1)
        assert called_with[0] is self.data
