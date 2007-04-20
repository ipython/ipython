#!/usr/bin/env python

import IPython.ipapi

ip = IPython.ipapi.get()

from string import Template
import sys

def toclip_w32(s):
    """ places contents of s to clipboard
    
    Needs pyvin32 to work:
    http://sourceforge.net/projects/pywin32/
    """
    import win32clipboard as cl
    import win32con
    cl.OpenClipboard()
    cl.EmptyClipboard()
    cl.SetClipboardText( s )
    cl.CloseClipboard()

try:
    import win32clipboard    
    toclip = toclip_w32
except ImportError:
    def toclip(s): pass
    

def render(tmpl):
    """ Render a template (as specified in string.Template docs) from ipython variables

    Example:
    
    $ import ipy_render
    $ my_name = 'Bob'  # %store this for convenience
    $ t_submission_form = "Submission report, author: $my_name"  # %store also
    $ render t_submission_form
    
    => returns "Submission report, author: Bob" and copies to clipboard on win32
    
    """
    
    s = Template(tmpl)
    res = s.substitute(ip.user_ns)
    toclip(res)
    return res

ip.to_user_ns('render')
    