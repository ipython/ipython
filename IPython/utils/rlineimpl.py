# -*- coding: utf-8 -*-
""" Imports and provides the 'correct' version of readline for the platform.

Readline is used throughout IPython as::

    import IPython.utils.rlineimpl as readline

In addition to normal readline stuff, this module provides have_readline
boolean and _outputfile variable used in IPython.utils.
"""

import sys
import warnings

try:
    from readline import *
    import readline as _rl
    have_readline = True
except ImportError:
    try:
        from pyreadline import *
        import pyreadline as _rl
        have_readline = True
    except ImportError:
        have_readline = False

if have_readline and hasattr(_rl, 'rlmain'):
    # patch add_history to allow for strings in pyreadline <= 1.5:
    # fix copied from pyreadline 1.6
    import pyreadline
    if pyreadline.release.version <= '1.5':
        def add_history(line):
            """add a line to the history buffer."""
            from pyreadline import lineobj
            if not isinstance(line, lineobj.TextLine):
                line = lineobj.TextLine(line)
            return _rl.add_history(line)

if sys.platform == 'win32' and have_readline:
    try:
        _outputfile=_rl.GetOutputFile()
    except AttributeError:
        print "Failed GetOutputFile"
        have_readline = False

# Test to see if libedit is being used instead of GNU readline.
# Thanks to Boyd Waters for this patch.
uses_libedit = False
if sys.platform == 'darwin' and have_readline:
    import commands
    # Boyd's patch had a 'while True' here, I'm always a little worried about
    # infinite loops with such code, so for now I'm taking a more conservative
    # approach. See https://bugs.launchpad.net/ipython/+bug/411599.
    for i in range(10):
        try:
            (status, result) = commands.getstatusoutput( "otool -L %s | grep libedit" % _rl.__file__ )
            break
        except IOError, (errno, strerror):
            if errno == 4:
                continue
            else:
                break

    if status == 0 and len(result) > 0:
        # we are bound to libedit - new in Leopard
        _rl.parse_and_bind("bind ^I rl_complete")
        warnings.warn("Leopard libedit detected - readline will not be well behaved "
            "including some crashes on tab completion, and incorrect history navigation. "
            "It is highly recommended that you install readline, "
            "which is easy_installable with: 'easy_install readline'",
            RuntimeWarning)
        uses_libedit = True


# the clear_history() function was only introduced in Python 2.4 and is
# actually optional in the readline API, so we must explicitly check for its
# existence.  Some known platforms actually don't have it.  This thread:
# http://mail.python.org/pipermail/python-dev/2003-August/037845.html
# has the original discussion.

if have_readline:
    try:
        _rl.clear_history
    except AttributeError:
        def clear_history(): pass
        _rl.clear_history = clear_history
