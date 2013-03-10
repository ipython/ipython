"""test IPython.embed_kernel()"""

#-------------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
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
import time

from contextlib import contextmanager
from subprocess import Popen, PIPE

import nose.tools as nt

from IPython.kernel import BlockingKernelClient
from IPython.utils import path, py3compat

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def setup():
    """setup temporary IPYTHONDIR for tests"""
    global IPYTHONDIR
    global env
    global save_get_ipython_dir
    
    IPYTHONDIR = tempfile.mkdtemp()

    env = os.environ.copy()
    env["IPYTHONDIR"] = IPYTHONDIR

    save_get_ipython_dir = path.get_ipython_dir
    path.get_ipython_dir = lambda : IPYTHONDIR


def teardown():
    path.get_ipython_dir = save_get_ipython_dir
    
    try:
        shutil.rmtree(IPYTHONDIR)
    except (OSError, IOError):
        # no such file
        pass


@contextmanager
def setup_kernel(cmd):
    """start an embedded kernel in a subprocess, and wait for it to be ready
    
    Returns
    -------
    kernel_manager: connected KernelManager instance
    """
    kernel = Popen([sys.executable, '-c', cmd], stdout=PIPE, stderr=PIPE, env=env)
    connection_file = os.path.join(IPYTHONDIR,
                                    'profile_default',
                                    'security',
                                    'kernel-%i.json' % kernel.pid
    )
    # wait for connection file to exist, timeout after 5s
    tic = time.time()
    while not os.path.exists(connection_file) and kernel.poll() is None and time.time() < tic + 10:
        time.sleep(0.1)
    
    if kernel.poll() is not None:
        o,e = kernel.communicate()
        e = py3compat.cast_unicode(e)
        raise IOError("Kernel failed to start:\n%s" % e)
    
    if not os.path.exists(connection_file):
        if kernel.poll() is None:
            kernel.terminate()
        raise IOError("Connection file %r never arrived" % connection_file)
    
    client = BlockingKernelClient(connection_file=connection_file)
    client.load_connection_file()
    client.start_channels()
    
    try:
        yield client
    finally:
        client.stop_channels()
        kernel.terminate()

def test_embed_kernel_basic():
    """IPython.embed_kernel() is basically functional"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'def go():',
        '    a=5',
        '    b="hi there"',
        '    embed_kernel()',
        'go()',
        '',
    ])
    
    with setup_kernel(cmd) as client:
        shell = client.shell_channel
    
        # oinfo a (int)
        msg_id = shell.object_info('a')
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_true(content['found'])
    
        msg_id = shell.execute("c=a*2")
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_equal(content['status'], u'ok')

        # oinfo c (should be 10)
        msg_id = shell.object_info('c')
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_true(content['found'])
        nt.assert_equal(content['string_form'], u'10')

def test_embed_kernel_namespace():
    """IPython.embed_kernel() inherits calling namespace"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'def go():',
        '    a=5',
        '    b="hi there"',
        '    embed_kernel()',
        'go()',
        '',
    ])
    
    with setup_kernel(cmd) as client:
        shell = client.shell_channel
    
        # oinfo a (int)
        msg_id = shell.object_info('a')
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_true(content['found'])
        nt.assert_equal(content['string_form'], u'5')

        # oinfo b (str)
        msg_id = shell.object_info('b')
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_true(content['found'])
        nt.assert_equal(content['string_form'], u'hi there')

        # oinfo c (undefined)
        msg_id = shell.object_info('c')
        msg = shell.get_msg(block=True, timeout=2)
        content = msg['content']
        nt.assert_false(content['found'])

def test_embed_kernel_reentrant():
    """IPython.embed_kernel() can be called multiple times"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'count = 0',
        'def go():',
        '    global count',
        '    embed_kernel()',
        '    count = count + 1',
        '',
        'while True:'
        '    go()',
        '',
    ])
    
    with setup_kernel(cmd) as client:
        shell = client.shell_channel
        for i in range(5):
            msg_id = shell.object_info('count')
            msg = shell.get_msg(block=True, timeout=2)
            content = msg['content']
            nt.assert_true(content['found'])
            nt.assert_equal(content['string_form'], unicode(i))
            
            # exit from embed_kernel
            shell.execute("get_ipython().exit_now = True")
            msg = shell.get_msg(block=True, timeout=2)
            time.sleep(0.2)


