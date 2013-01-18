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
import tempfile

from Queue import Empty
from contextlib import contextmanager
from subprocess import PIPE

import nose.tools as nt

from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.zmq.tests.test_message_spec import execute, flush_channels
from IPython.testing import decorators as dec
from IPython.utils import path, py3compat

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

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
    KM = BlockingKernelManager()

    KM.start_kernel(stdout=PIPE, stderr=PIPE)
    KM.start_channels()
    
    # wait for kernel to be ready
    KM.shell_channel.execute("import sys")
    KM.shell_channel.get_msg(block=True, timeout=5)
    flush_channels(KM)
    try:
        yield KM
    finally:
        KM.stop_channels()
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


def _check_mp_mode(km, expected=False, stream="stdout"):
    execute(km=km, code="import sys")
    flush_channels(km)
    msg_id, content = execute(km=km, code="print (sys.%s._check_mp_mode())" % stream)
    stdout, stderr = assemble_output(km.iopub_channel)
    nt.assert_equal(eval(stdout.strip()), expected)


def test_simple_print():
    """simple print statement in kernel"""
    with new_kernel() as km:
        iopub = km.iopub_channel
        msg_id, content = execute(km=km, code="print ('hi')")
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, 'hi\n')
        nt.assert_equal(stderr, '')
        _check_mp_mode(km, expected=False)
    print ('hello')


def test_subprocess_print():
    """printing from forked mp.Process"""
    with new_kernel() as km:
        iopub = km.iopub_channel
        
        _check_mp_mode(km, expected=False)
        flush_channels(km)
        np = 5
        code = '\n'.join([
            "import multiprocessing as mp",
            "def f(x):",
            "    print('hello',x)",
            "pool = [mp.Process(target=f,args=(i,)) for i in range(%i)]" % np,
            "for p in pool: p.start()",
            "for p in pool: p.join()"
        ])
        
        expected = '\n'.join([
            "hello %s" % i for i in range(np)
        ]) + '\n'
        
        msg_id, content = execute(km=km, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout.count("hello"), np, stdout)
        for n in range(np):
            nt.assert_equal(stdout.count(str(n)), 1, stdout)
        nt.assert_equal(stderr, '')
        _check_mp_mode(km, expected=False)
        _check_mp_mode(km, expected=False, stream="stderr")


def test_subprocess_noprint():
    """mp.Process without print doesn't trigger iostream mp_mode"""
    with new_kernel() as km:
        iopub = km.iopub_channel
        
        np = 5
        code = '\n'.join([
            "import multiprocessing as mp",
            "def f(x):",
            "    return x",
            "pool = [mp.Process(target=f,args=(i,)) for i in range(%i)]" % np,
            "for p in pool: p.start()",
            "for p in pool: p.join()"
        ])
        
        msg_id, content = execute(km=km, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, '')
        nt.assert_equal(stderr, '')

        _check_mp_mode(km, expected=False)
        _check_mp_mode(km, expected=False, stream="stderr")


def test_subprocess_error():
    """error in mp.Process doesn't crash"""
    with new_kernel() as km:
        iopub = km.iopub_channel
        
        code = '\n'.join([
            "import multiprocessing as mp",
            "def f():",
            "    return 1/0",
            "p = mp.Process(target=f)",
            "p.start()",
            "p.join()",
        ])
        
        msg_id, content = execute(km=km, code=code)
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, '')
        nt.assert_true("ZeroDivisionError" in stderr, stderr)

        _check_mp_mode(km, expected=False)
        _check_mp_mode(km, expected=False, stream="stderr")

