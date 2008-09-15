# encoding: utf-8
# -*- test-case-name: IPython.kernel.test.test_contexts -*-
"""Context managers for IPython.

Python 2.5 introduced the `with` statement, which is based on the context
manager protocol.  This module offers a few context managers for common cases,
which can also be useful as templates for writing new, application-specific
managers.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import linecache
import sys

from twisted.internet.error import ConnectionRefusedError

from IPython.ultraTB import _fixed_getinnerframes, findsource
from IPython import ipapi

from IPython.kernel import error

#---------------------------------------------------------------------------
# Utility functions needed by all context managers.
#---------------------------------------------------------------------------

def remote():
    """Raises a special exception meant to be caught by context managers.
    """
    m = 'Special exception to stop local execution of parallel code.'
    raise error.StopLocalExecution(m)


def strip_whitespace(source,require_remote=True):
    """strip leading whitespace from input source.

    :Parameters:

    """
    remote_mark = 'remote()'
    # Expand tabs to avoid any confusion.
    wsource = [l.expandtabs(4) for l in source]
    # Detect the indentation level
    done = False
    for line in wsource:
        if line.isspace():
            continue
        for col,char in enumerate(line):
            if char != ' ':
                done = True
                break
        if done:
            break
    # Now we know how much leading space there is in the code.  Next, we
    # extract up to the first line that has less indentation.
    # WARNINGS: we skip comments that may be misindented, but we do NOT yet
    # detect triple quoted strings that may have flush left text.
    for lno,line in enumerate(wsource):
        lead = line[:col]
        if lead.isspace():
            continue
        else:
            if not lead.lstrip().startswith('#'):
                break
    # The real 'with' source is up to lno
    src_lines = [l[col:] for l in wsource[:lno+1]]

    # Finally, check that the source's first non-comment line begins with the
    # special call 'remote()'
    if require_remote:
        for nline,line in enumerate(src_lines):
            if line.isspace() or line.startswith('#'):
                continue
            if line.startswith(remote_mark):
                break
            else:
                raise ValueError('%s call missing at the start of code' %
                                 remote_mark)
        out_lines = src_lines[nline+1:]
    else:
        # If the user specified that the remote() call wasn't mandatory
        out_lines = src_lines

    # src = ''.join(out_lines)  # dbg
    #print 'SRC:\n<<<<<<<>>>>>>>\n%s<<<<<>>>>>>' % src  # dbg
    return ''.join(out_lines)

class RemoteContextBase(object):
    def __init__(self):
        self.ip = ipapi.get()

    def _findsource_file(self,f):
        linecache.checkcache()
        s = findsource(f.f_code)
        lnum = f.f_lineno
        wsource = s[0][f.f_lineno:]
        return strip_whitespace(wsource)

    def _findsource_ipython(self,f):
        from IPython import ipapi
        self.ip = ipapi.get()
        buf = self.ip.IP.input_hist_raw[-1].splitlines()[1:]
        wsource = [l+'\n' for l in buf ]

        return strip_whitespace(wsource)

    def findsource(self,frame):
        local_ns = frame.f_locals
        global_ns = frame.f_globals
        if frame.f_code.co_filename == '<ipython console>':
            src = self._findsource_ipython(frame)
        else:
            src = self._findsource_file(frame)
        return src

    def __enter__(self):
        raise NotImplementedError

    def __exit__ (self, etype, value, tb):
        if issubclass(etype,error.StopLocalExecution):
            return True

class RemoteMultiEngine(RemoteContextBase):
    def __init__(self,mec):
        self.mec = mec
        RemoteContextBase.__init__(self)

    def __enter__(self):
        src = self.findsource(sys._getframe(1))
        return self.mec.execute(src)
