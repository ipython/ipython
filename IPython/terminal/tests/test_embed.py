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

#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------

_sample_embed = """
from __future__ import print_function
import IPython

a = 3
b = 14
print(a, '.', b)

IPython.embed()

print 'bye!'
"""

def test_ipython_embed():
    """test that `ipython [subcommand] --help-all` works"""
    #with TempFile as f:
    #    f.write("some embed case goes here")

    # run `python file_with_embed.py`
    fname = '/home/pi/code/workspace/rambles/test_embed.py'
    cmd = [sys.executable, fname]

    #p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    print "\nhere's the command:", cmd
    _, out, p = process_handler(cmd,
            lambda p: (p.stdin.write("exit\r"), p.communicate()[:], p))
    print out[1]
    nt.assert_equal(p.returncode, 0)
    nt.assert_equal(p.returncode, 0)
#out, err, rc = tt.get_output_error_code(cmd)

