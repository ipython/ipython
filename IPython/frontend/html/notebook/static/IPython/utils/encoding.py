# coding: utf-8
"""
Utilities for dealing with text encodings
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import sys
import locale

# to deal with the possibility of sys.std* not being a stream at all
def get_stream_enc(stream, default=None):
    """Return the given stream's encoding or a default.

    There are cases where sys.std* might not actually be a stream, so
    check for the encoding attribute prior to returning it, and return
    a default if it doesn't exist or evaluates as False. `default'
    is None if not provided.
    """
    if not hasattr(stream, 'encoding') or not stream.encoding:
        return default
    else:
        return stream.encoding

# Less conservative replacement for sys.getdefaultencoding, that will try
# to match the environment.
# Defined here as central function, so if we find better choices, we
# won't need to make changes all over IPython.
def getdefaultencoding():
    """Return IPython's guess for the default encoding for bytes as text.

    Asks for stdin.encoding first, to match the calling Terminal, but that
    is often None for subprocesses.  Fall back on locale.getpreferredencoding()
    which should be a sensible platform default (that respects LANG environment),
    and finally to sys.getdefaultencoding() which is the most conservative option,
    and usually ASCII.
    """
    enc = get_stream_enc(sys.stdin)
    if not enc or enc=='ascii':
        try:
            # There are reports of getpreferredencoding raising errors
            # in some cases, which may well be fixed, but let's be conservative here.
            enc = locale.getpreferredencoding()
        except Exception:
            pass
    return enc or sys.getdefaultencoding()

DEFAULT_ENCODING = getdefaultencoding()
