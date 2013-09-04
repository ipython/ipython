"""test the IPython Kernel"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import shutil
import sys
import tempfile

from contextlib import contextmanager
from subprocess import PIPE

import nose.tools as nt

from IPython.kernel import KernelManager
from IPython.kernel.tests.test_message_spec import execute, flush_channels
from IPython.testing import decorators as dec, tools as tt
from IPython.utils import path, py3compat

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------
IPYTHONDIR = None
save_env = None
save_get_ipython_dir = None

STARTUP_TIMEOUT = 60
TIMEOUT = 15

def setup():
    """setup temporary IPYTHONDIR for tests"""
    global IPYTHONDIR
    global save_env
    global save_get_ipython_dir

    IPYTHONDIR = tempfile.mkdtemp()

    save_env = os.environ.copy()
    os.environ["IPYTHONDIR"] = IPYTHONDIR

    save_get_ipython_dir = path.get_ipython_dir
    path.get_ipython_dir = lambda : IPYTHONDIR


def teardown():
    path.get_ipython_dir = save_get_ipython_dir
    os.environ = save_env

    try:
        shutil.rmtree(IPYTHONDIR)
    except (OSError, IOError):
        # no such file
        pass


@contextmanager
def new_kernel():
    """start a kernel in a subprocess, and wait for it to be ready

    Returns
    -------
    kernel_manager: connected KernelManager instance
    """
    KM = KernelManager()

    KM.start_kernel(stdout=PIPE, stderr=PIPE)
    KC = KM.client()
    KC.start_channels()

    # wait for kernel to be ready
    KC.shell_channel.execute("import sys")
    KC.shell_channel.get_msg(block=True, timeout=STARTUP_TIMEOUT)
    flush_channels(KC)
    try:
        yield KC
    finally:
        KC.stop_channels()
        KM.shutdown_kernel()


def assemble_output(iopub):
    """assemble stdout/err from an execution"""
    stdout = ''
    stderr = ''
    while True:
        msg = iopub.get_msg(block=True, timeout=1)
        msg_type = msg['msg_type']
        content = msg['content']
        if msg_type == 'status' and content['execution_state'] == 'idle':
            # idle message signals end of output
            break
        elif msg['msg_type'] == 'stream':
            if content['name'] == 'stdout':
                stdout = stdout + content['data']
            elif content['name'] == 'stderr':
                stderr = stderr + content['data']
            else:
                raise KeyError("bad stream: %r" % content['name'])
        else:
            # other output, ignored
            pass
    return stdout, stderr


def _check_mp_mode(kc, expected=False, stream="stdout"):
    execute(kc=kc, code="import sys")
    flush_channels(kc)
    msg_id, content = execute(kc=kc, code="print (sys.%s._check_mp_mode())" % stream)
    stdout, stderr = assemble_output(kc.iopub_channel)
    nt.assert_equal(eval(stdout.strip()), expected)


# printing tests

def test_simple_print():
    """simple print statement in kernel"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel
        msg_id, content = execute(kc=kc, code="print ('hi')")
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, 'hi\n')
        nt.assert_equal(stderr, '')
        _check_mp_mode(kc, expected=False)


@dec.knownfailureif(sys.platform == 'win32', "subprocess prints fail on Windows")
def test_subprocess_print():
    """printing from forked mp.Process"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel

        _check_mp_mode(kc, expected=False)
        flush_channels(kc)
        np = 5
        code = '\n'.join([
            "from __future__ import print_function",
            "import multiprocessing as mp",
            "pool = [mp.Process(target=print, args=('hello', i,)) for i in range(%i)]" % np,
            "for p in pool: p.start()",
            "for p in pool: p.join()"
        ])

        expected = '\n'.join([
            "hello %s" % i for i in range(np)
        ]) + '\n'

        msg_id, content = execute(kc=kc, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout.count("hello"), np, stdout)
        for n in range(np):
            nt.assert_equal(stdout.count(str(n)), 1, stdout)
        nt.assert_equal(stderr, '')
        _check_mp_mode(kc, expected=False)
        _check_mp_mode(kc, expected=False, stream="stderr")


def test_subprocess_noprint():
    """mp.Process without print doesn't trigger iostream mp_mode"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel

        np = 5
        code = '\n'.join([
            "import multiprocessing as mp",
            "pool = [mp.Process(target=range, args=(i,)) for i in range(%i)]" % np,
            "for p in pool: p.start()",
            "for p in pool: p.join()"
        ])

        msg_id, content = execute(kc=kc, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, '')
        nt.assert_equal(stderr, '')

        _check_mp_mode(kc, expected=False)
        _check_mp_mode(kc, expected=False, stream="stderr")


@dec.knownfailureif(sys.platform == 'win32', "subprocess prints fail on Windows")
def test_subprocess_error():
    """error in mp.Process doesn't crash"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel

        code = '\n'.join([
            "import multiprocessing as mp",
            "p = mp.Process(target=int, args=('hi',))",
            "p.start()",
            "p.join()",
        ])

        msg_id, content = execute(kc=kc, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, '')
        nt.assert_true("ValueError" in stderr, stderr)

        _check_mp_mode(kc, expected=False)
        _check_mp_mode(kc, expected=False, stream="stderr")

# raw_input tests

def test_raw_input():
    """test [raw_]input"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel

        input_f = "input" if py3compat.PY3 else "raw_input"
        theprompt = "prompt> "
        code = 'print({input_f}("{theprompt}"))'.format(**locals())
        msg_id = kc.execute(code, allow_stdin=True)
        msg = kc.get_stdin_msg(block=True, timeout=TIMEOUT)
        nt.assert_equal(msg['header']['msg_type'], u'input_request')
        content = msg['content']
        nt.assert_equal(content['prompt'], theprompt)
        text = "some text"
        kc.input(text)
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        nt.assert_equal(reply['content']['status'], 'ok')
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, text + "\n")


@dec.skipif(py3compat.PY3)
def test_eval_input():
    """test input() on Python 2"""
    with new_kernel() as kc:
        iopub = kc.iopub_channel

        input_f = "input" if py3compat.PY3 else "raw_input"
        theprompt = "prompt> "
        code = 'print(input("{theprompt}"))'.format(**locals())
        msg_id = kc.execute(code, allow_stdin=True)
        msg = kc.get_stdin_msg(block=True, timeout=TIMEOUT)
        nt.assert_equal(msg['header']['msg_type'], u'input_request')
        content = msg['content']
        nt.assert_equal(content['prompt'], theprompt)
        kc.input("1+1")
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        nt.assert_equal(reply['content']['status'], 'ok')
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, "2\n")


def test_help_output():
    """ipython kernel --help-all works"""
    tt.help_all_output_test('kernel')
