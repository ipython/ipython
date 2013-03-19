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
from .utils import highlight2latex
from .utils import get_lines
from .latex_transformer import rm_math_space

from .config import GlobalConfigurable

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import List

#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class ConfigurableFilter(GlobalConfigurable):
    """Configurable Jinja Filter"""

    def __init__(self, config=None, **kw):
        super(ConfigurableFilter, self).__init__(config=config, **kw)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError('should be implemented by subclass')


class FilterDataType(ConfigurableFilter):
    """ return the preferd displayed format
    """

    def __call__(self, output):
        """ return the first availlable format in priority """
        for fmt in self.display_data_priority:
            if fmt in output:
                return [fmt]
        return []



def rm_fake(strng):
    return strng.replace('/files/', '')

def rm_dollars(strng):
    return strng.strip('$')

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

