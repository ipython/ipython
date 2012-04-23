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

from subprocess import Popen, PIPE

import nose.tools as nt

from IPython.zmq.blockingkernelmanager import BlockingKernelManager
from IPython.utils import path


#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def setup():
    """setup temporary IPYTHONDIR for tests"""
    global IPYTHONDIR
    global env
    global save_get_ipython_dir
    
    IPYTHONDIR = tempfile.mkdtemp()
    env = dict(IPYTHONDIR=IPYTHONDIR)
    save_get_ipython_dir = path.get_ipython_dir
    path.get_ipython_dir = lambda : IPYTHONDIR


def teardown():
    path.get_ipython_dir = save_get_ipython_dir
    
    try:
        shutil.rmtree(IPYTHONDIR)
    except (OSError, IOError):
        # no such file
        pass


def _launch_kernel(cmd):
    """start an embedded kernel in a subprocess, and wait for it to be ready
    
    Returns
    -------
    kernel, kernel_manager: Popen instance and connected KernelManager
    """
    kernel = Popen([sys.executable, '-c', cmd], stdout=PIPE, stderr=PIPE, env=env)
    connection_file = os.path.join(IPYTHONDIR,
                                    'profile_default',
                                    'security',
                                    'kernel-%i.json' % kernel.pid
    )
    # wait for connection file to exist, timeout after 5s
    tic = time.time()
    while not os.path.exists(connection_file) and kernel.poll() is None and time.time() < tic + 5:
        time.sleep(0.1)
    
    if not os.path.exists(connection_file):
        if kernel.poll() is None:
            kernel.terminate()
        raise IOError("Connection file %r never arrived" % connection_file)
    
    if kernel.poll() is not None:
        raise IOError("Kernel failed to start")
    
    km = BlockingKernelManager(connection_file=connection_file)
    km.load_connection_file()
    km.start_channels()
    
    return kernel, km

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
    
    kernel, km = _launch_kernel(cmd)
    shell = km.shell_channel
    
    # oinfo a (int)
    msg_id = shell.object_info('a')
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_true(content['found'])
    
    msg_id = shell.execute("c=a*2")
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_equals(content['status'], u'ok')

    # oinfo c (should be 10)
    msg_id = shell.object_info('c')
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_true(content['found'])
    nt.assert_equals(content['string_form'], u'10')

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
    
    kernel, km = _launch_kernel(cmd)
    shell = km.shell_channel
    
    # oinfo a (int)
    msg_id = shell.object_info('a')
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_true(content['found'])
    nt.assert_equals(content['string_form'], u'5')

    # oinfo b (str)
    msg_id = shell.object_info('b')
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_true(content['found'])
    nt.assert_equals(content['string_form'], u'hi there')

    # oinfo c (undefined)
    msg_id = shell.object_info('c')
    msg = shell.get_msg(block=True, timeout=2)
    content = msg['content']
    nt.assert_false(content['found'])

