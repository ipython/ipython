#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from __future__ import absolute_import

# Stdlib imports
import re

from IPython.utils.text import indent
from markdown import markdown
from .utils import remove_ansi
from .utils import highlight, ansi2html
from .utils import markdown2latex
#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
def rm_fake(strng):
    return strng.replace('/files/', '')

def python_comment(string):
    return '# '+'\n# '.join(string.split('\n'))

LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash'),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots'),
)

def escape_tex(value):
    newval = value
    for pattern, replacement in LATEX_SUBS:
        newval = pattern.sub(replacement, newval)
    return newval

