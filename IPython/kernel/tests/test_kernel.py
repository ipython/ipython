# coding: utf-8
"""test the IPython Kernel"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import os.path
import sys

import nose.tools as nt

from IPython.testing import decorators as dec, tools as tt
from IPython.utils import py3compat
from IPython.utils.path import locate_profile
from IPython.utils.tempdir import TemporaryDirectory

from .utils import (new_kernel, kernel, TIMEOUT, assemble_output, execute,
                    flush_channels, wait_for_idle)


def _check_mp_mode(kc, expected=False, stream="stdout"):
    execute(kc=kc, code="import sys")
    flush_channels(kc)
    msg_id, content = execute(kc=kc, code="print (sys.%s._check_mp_mode())" % stream)
    stdout, stderr = assemble_output(kc.iopub_channel)
    nt.assert_equal(eval(stdout.strip()), expected)


# printing tests

def test_simple_print():
    """simple print statement in kernel"""
    with kernel() as kc:
        iopub = kc.iopub_channel
        msg_id, content = execute(kc=kc, code="print ('hi')")
        stdout, stderr = assemble_output(iopub)
        nt.assert_equal(stdout, 'hi\n')
        nt.assert_equal(stderr, '')
        _check_mp_mode(kc, expected=False)


def test_sys_path():
    """test that sys.path doesn't get messed up by default"""
    with kernel() as kc:
        msg_id, content = execute(kc=kc, code="import sys; print (repr(sys.path[0]))")
        stdout, stderr = assemble_output(kc.iopub_channel)
        nt.assert_equal(stdout, "''\n")

def test_sys_path_profile_dir():
    """test that sys.path doesn't get messed up when `--profile-dir` is specified"""
    
    with new_kernel(['--profile-dir', locate_profile('default')]) as kc:
        msg_id, content = execute(kc=kc, code="import sys; print (repr(sys.path[0]))")
        stdout, stderr = assemble_output(kc.iopub_channel)
        nt.assert_equal(stdout, "''\n")

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
    with kernel() as kc:
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
    with kernel() as kc:
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
    with kernel() as kc:
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


def test_save_history():
    # Saving history from the kernel with %hist -f was failing because of
    # unicode problems on Python 2.
    with kernel() as kc, TemporaryDirectory() as td:
        file = os.path.join(td, 'hist.out')
        execute(u'a=1', kc=kc)
        wait_for_idle(kc)
        execute(u'b=u"abcþ"', kc=kc)
        wait_for_idle(kc)
        _, reply = execute("%hist -f " + file, kc=kc)
        nt.assert_equal(reply['status'], 'ok')
        with io.open(file, encoding='utf-8') as f:
            content = f.read()
        nt.assert_in(u'a=1', content)
        nt.assert_in(u'b=u"abcþ"', content)

def test_help_output():
    """ipython kernel --help-all works"""
    tt.help_all_output_test('kernel')

def test_is_complete():
    with kernel() as kc:
        # There are more test cases for this in core - here we just check
        # that the kernel exposes the interface correctly.
        kc.is_complete('2+2')
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        assert reply['content']['status'] == 'complete'

        # SyntaxError should mean it's complete
        kc.is_complete('raise = 2')
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        assert reply['content']['status'] == 'invalid'
        
        kc.is_complete('a = [1,\n2,')
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        assert reply['content']['status'] == 'incomplete'
        assert reply['content']['indent'] == ''

def test_complete():
    with kernel() as kc:
        execute(u'a = 1', kc=kc)
        wait_for_idle(kc)
        cell = 'import IPython\nb = a.'
        kc.complete(cell)
        reply = kc.get_shell_msg(block=True, timeout=TIMEOUT)
        c = reply['content']
        nt.assert_equal(c['status'], 'ok')
        nt.assert_equal(c['cursor_start'], cell.find('a.'))
        nt.assert_equal(c['cursor_end'], cell.find('a.') + 2)
        matches = c['matches']
        nt.assert_greater(len(matches), 0)
        for match in matches:
            nt.assert_equal(match[:2], 'a.')
