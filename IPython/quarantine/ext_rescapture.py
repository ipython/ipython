# -*- coding: utf-8 -*-
""" IPython extension: new prefilters for output grabbing

Provides

var = %magic blah blah

var = !ls
"""

from IPython.core import ipapi
from IPython.core.error import TryNext
from IPython.utils.text import make_quoted_expr
from IPython.utils.genutils import *

ip = ipapi.get()

import re

def hnd_magic(line,mo):
    """ Handle a = %mymagic blah blah """
    var = mo.group('varname')
    cmd = mo.group('cmd')
    expr = make_quoted_expr(cmd)
    return itpl('$var = get_ipython().magic($expr)')

def hnd_syscmd(line,mo):
    """ Handle a = !ls """
    var = mo.group('varname')
    cmd = mo.group('cmd')
    expr = make_quoted_expr(itpl("sc -l =$cmd"))
    return itpl('$var = get_ipython().magic($expr)')

def install_re_handler(pat, hnd):
    ip.meta.re_prefilters.append((re.compile(pat), hnd))

def init_handlers():

    ip.meta.re_prefilters = []

    install_re_handler('(?P<varname>[\w\.]+)\s*=\s*%(?P<cmd>.*)',
                       hnd_magic
                       )

    install_re_handler('(?P<varname>[\w\.]+)\s*=\s*!(?P<cmd>.*)',
                       hnd_syscmd
                       )

init_handlers()

def regex_prefilter_f(self,line):
    for pat, handler in ip.meta.re_prefilters:
        mo = pat.match(line)
        if mo:
            return handler(line,mo)

    raise TryNext

ip.set_hook('input_prefilter', regex_prefilter_f)
