"""Test embedding of IPython"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import nose.tools as nt
from IPython.utils.process import process_handler
from IPython.utils.tempdir import NamedFileInTemporaryDirectory

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

_sample_embed = b"""
from __future__ import print_function
import IPython

a = 3
b = 14
print(a, '.', b)

IPython.embed()

print('bye!')
"""

_exit = b"exit\r"

def test_ipython_embed():
    """test that `IPython.embed()` works"""
    with NamedFileInTemporaryDirectory('file_with_embed.py') as f:
        f.write(_sample_embed)
        f.flush()

        # run `python file_with_embed.py`
        cmd = [sys.executable, f.name]

        _, out, p = process_handler(cmd,
                lambda p: (p.stdin.write(_exit), p.communicate()[:], p))
        std = out[0].decode('UTF-8')
        nt.assert_equal(p.returncode, 0)
        nt.assert_in('3 . 14', std)
        nt.assert_in('IPython', std)
        nt.assert_in('bye!', std)

