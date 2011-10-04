""" IPython extension: Render templates from variables and paste to clipbard """

from IPython.core import ipapi

ip = ipapi.get()

from string import Template
import sys,os

from IPython.external.Itpl import itplns

def toclip_w32(s):
    """ Places contents of s to clipboard

    Needs pyvin32 to work:
    http://sourceforge.net/projects/pywin32/
    """
    import win32clipboard as cl
    import win32con
    cl.OpenClipboard()
    cl.EmptyClipboard()
    cl.SetClipboardText( s.replace('\n','\r\n' ))
    cl.CloseClipboard()

try:
    import win32clipboard
    toclip = toclip_w32
except ImportError:
    def toclip(s): pass


def render(tmpl):
    """ Render a template (Itpl format) from ipython variables

    Example:

    $ import ipy_render
    $ my_name = 'Bob'  # %store this for convenience
    $ t_submission_form = "Submission report, author: $my_name"  # %store also
    $ render t_submission_form

    => returns "Submission report, author: Bob" and copies to clipboard on win32

    # if template exist as a file, read it. Note: ;f hei vaan => f("hei vaan")
    $ ;render c:/templates/greeting.txt

    Template examples (Ka-Ping Yee's Itpl library):

    Here is a $string.
    Here is a $module.member.
    Here is an $object.member.
    Here is a $functioncall(with, arguments).
    Here is an ${arbitrary + expression}.
    Here is an $array[3] member.
    Here is a $dictionary['member'].
    """

    if os.path.isfile(tmpl):
        tmpl = open(tmpl).read()

    res = itplns(tmpl, ip.user_ns)
    toclip(res)
    return res

ip.push('render')
