# -*- coding: utf-8 -*-
""" Imports and provides the 'correct' version of readline for the platform.

Readline is used throughout IPython as::

    import IPython.utils.rlineimpl as readline

In addition to normal readline stuff, this module provides have_readline
boolean and _outputfile variable used in IPython.utils.
"""

import sys
import warnings

# priority: pyrepl > readline > pyreadline
have_pyrepl = False
try:
    from pyrepl.readline import *
    import pyrepl.readline as _rl
    have_readline = True
    have_pyrepl = True
except ImportError:
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

if (sys.platform == 'win32' or sys.platform == 'cli') and have_readline:
    try:
        _outputfile=_rl.GetOutputFile()
    except AttributeError:
        warnings.warn("Failed GetOutputFile")
        have_readline = False

# Test to see if libedit is being used instead of GNU readline.
# Thanks to Boyd Waters for the original patch.
uses_libedit = False

if have_readline:
    # Official Python docs state that 'libedit' is in the docstring for libedit readline:
    uses_libedit = _rl.__doc__ and 'libedit' in _rl.__doc__
    # Note that many non-System Pythons also do not use proper readline,
    # but do not report libedit at all, nor are they linked dynamically against libedit.
    # known culprits of this include: EPD, Fink
    # There is not much we can do to detect this, until we find a specific failure
    # case, rather than relying on the readline module to self-identify as broken.

if uses_libedit and sys.platform == 'darwin':
    _rl.parse_and_bind("bind ^I rl_complete")
    warnings.warn('\n'.join(['', "*"*78,
        "libedit detected - readline will not be well behaved, including but not limited to:",
        "   * crashes on tab completion",
        "   * incorrect history navigation",
        "   * corrupting long-lines",
        "   * failure to wrap or indent lines properly",
        "It is highly recommended that you install pyrepl, which is pip installable:",
        "     pip install pyrepl",
        "*"*78]),
        RuntimeWarning)
elif have_readline and not have_pyrepl and not sys.platform in ('win32', 'cli'):
    warnings.warn('\n'.join(["",
        "Python readline has a bug, where C-c to interrupt C-r reverse-i search",
        "can leave hidden input. Make sure you use C-g to end C-r search, and not C-c.",
        "It is highly recommended that you install pyrepl, which is pip installable:",
        "     pip install pyrepl",
        ]),
    RuntimeWarning)

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
