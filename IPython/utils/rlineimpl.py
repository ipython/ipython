# -*- coding: utf-8 -*-
""" Imports and provides the 'correct' version of readline for the platform.

Readline is used throughout IPython as::

    import IPython.utils.rlineimpl as readline

In addition to normal readline stuff, this module provides have_readline
boolean and _outputfile variable used in IPython.utils.
"""

import re
import sys
import time
import warnings

from subprocess import Popen, PIPE

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
# Thanks to Boyd Waters for the original patch.
uses_libedit = False
if sys.platform == 'darwin' and have_readline:
    # Previously this used commands.getstatusoutput, which uses os.popen.
    # Switching to subprocess.Popen, and exponential falloff for EINTR
    # seems to make this better behaved in environments such as PyQt and gdb
    dt = 1e-3
    while dt < 1:
        p = Popen(['otool', '-L', _rl.__file__], stdout=PIPE, stderr=PIPE)
        otool,err = p.communicate()

        if p.returncode == 4:
            # EINTR
            time.sleep(dt)
            dt *= 2
            continue
        elif p.returncode:
            warnings.warn("libedit detection failed: %s"%err)
            break
        else:
            break

    if p.returncode == 0 and re.search(r'/libedit[\.\d+]*\.dylib\s', otool):
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
