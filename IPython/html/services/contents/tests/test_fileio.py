# encoding: utf-8
"""Tests for file IO"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io as stdlib_io
import os.path
import stat

import nose.tools as nt

from IPython.testing.decorators import skip_win32
from ..fileio import atomic_writing

from IPython.utils.tempdir import TemporaryDirectory

umask = 0

def test_atomic_writing():
    class CustomExc(Exception): pass

    with TemporaryDirectory() as td:
        f1 = os.path.join(td, 'penguin')
        with stdlib_io.open(f1, 'w') as f:
            f.write(u'Before')
        
        if os.name != 'nt':
            os.chmod(f1, 0o701)
            orig_mode = stat.S_IMODE(os.stat(f1).st_mode)

        f2 = os.path.join(td, 'flamingo')
        try:
            os.symlink(f1, f2)
            have_symlink = True
        except (AttributeError, NotImplementedError, OSError):
            # AttributeError: Python doesn't support it
            # NotImplementedError: The system doesn't support it
            # OSError: The user lacks the privilege (Windows)
            have_symlink = False

        with nt.assert_raises(CustomExc):
            with atomic_writing(f1) as f:
                f.write(u'Failing write')
                raise CustomExc

        # Because of the exception, the file should not have been modified
        with stdlib_io.open(f1, 'r') as f:
            nt.assert_equal(f.read(), u'Before')

        with atomic_writing(f1) as f:
            f.write(u'Overwritten')

        with stdlib_io.open(f1, 'r') as f:
            nt.assert_equal(f.read(), u'Overwritten')

        if os.name != 'nt':
            mode = stat.S_IMODE(os.stat(f1).st_mode)
            nt.assert_equal(mode, orig_mode)

        if have_symlink:
            # Check that writing over a file preserves a symlink
            with atomic_writing(f2) as f:
                f.write(u'written from symlink')
            
            with stdlib_io.open(f1, 'r') as f:
                nt.assert_equal(f.read(), u'written from symlink')

def _save_umask():
    global umask
    umask = os.umask(0)
    os.umask(umask)

def _restore_umask():
    os.umask(umask)

@skip_win32
@nt.with_setup(_save_umask, _restore_umask)
def test_atomic_writing_umask():
    with TemporaryDirectory() as td:
        os.umask(0o022)
        f1 = os.path.join(td, '1')
        with atomic_writing(f1) as f:
            f.write(u'1')
        mode = stat.S_IMODE(os.stat(f1).st_mode)
        nt.assert_equal(mode, 0o644, '{:o} != 644'.format(mode))

        os.umask(0o057)
        f2 = os.path.join(td, '2')
        with atomic_writing(f2) as f:
            f.write(u'2')
        mode = stat.S_IMODE(os.stat(f2).st_mode)
        nt.assert_equal(mode, 0o620, '{:o} != 620'.format(mode))


def test_atomic_writing_newlines():
    with TemporaryDirectory() as td:
        path = os.path.join(td, 'testfile')
        
        lf = u'a\nb\nc\n'
        plat = lf.replace(u'\n', os.linesep)
        crlf = lf.replace(u'\n', u'\r\n')
        
        # test default
        with stdlib_io.open(path, 'w') as f:
            f.write(lf)
        with stdlib_io.open(path, 'r', newline='') as f:
            read = f.read()
        nt.assert_equal(read, plat)
        
        # test newline=LF
        with stdlib_io.open(path, 'w', newline='\n') as f:
            f.write(lf)
        with stdlib_io.open(path, 'r', newline='') as f:
            read = f.read()
        nt.assert_equal(read, lf)
        
        # test newline=CRLF
        with atomic_writing(path, newline='\r\n') as f:
            f.write(lf)
        with stdlib_io.open(path, 'r', newline='') as f:
            read = f.read()
        nt.assert_equal(read, crlf)
        
        # test newline=no convert
        text = u'crlf\r\ncr\rlf\n'
        with atomic_writing(path, newline='') as f:
            f.write(text)
        with stdlib_io.open(path, 'r', newline='') as f:
            read = f.read()
        nt.assert_equal(read, text)
