# -*- coding: utf-8 -*-
""" Imports and provides the 'correct' version of readline for the platform.

Readline is used throughout IPython as 'import IPython.rlineimpl as readline'.

In addition to normal readline stuff, this module provides have_readline
boolean and _outputfile variable used in genutils.

$Id: Magic.py 1096 2006-01-28 20:08:02Z vivainio $"""

import sys

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
    (status, result) = commands.getstatusoutput( "otool -L %s | grep libedit" % _rl.__file__ )
    if status == 0 and len(result) > 0:
        # we are bound to libedit - new in Leopard
        _rl.parse_and_bind("bind ^I rl_complete")
        print "Leopard libedit detected."
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