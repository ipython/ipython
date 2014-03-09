# -*- coding: utf-8 -*-
""" Imports and provides the 'correct' version of readline for the platform.

Readline is used throughout IPython as::

    import IPython.utils.rlineimpl as readline

In addition to normal readline stuff, this module provides have_readline
boolean and _outputfile variable used in IPython.utils.
"""

import sys
import warnings

_rlmod_names = ['gnureadline', 'readline']

have_readline = False
for _rlmod_name in _rlmod_names:
    try:
        # import readline as _rl
        _rl = __import__(_rlmod_name)
        # from readline import *
        globals().update({k:v for k,v in _rl.__dict__.items() if not k.startswith('_')})
    except ImportError:
        pass
    else:
        have_readline = True
        break

if have_readline and (sys.platform == 'win32' or sys.platform == 'cli'):
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
        "It is highly recommended that you install gnureadline, which is installable with:",
        "     pip install gnureadline",
        "*"*78]),
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
