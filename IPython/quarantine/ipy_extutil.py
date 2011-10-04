""" IPython extension management tools.

After installation, you'll have the 'extutil' object in your namespace.
to.
"""

# for the purposes of this module, every module that has the name 'ip' globally
# installed as below is an IPython extension

from IPython.core import ipapi
ip = ipapi.get()
from IPython.core.iplib import InteractiveShell

import sys,textwrap,inspect

def indent(s, ind= '    '):
    return '\n'.join([ind +l for l in s.splitlines()])

class ExtUtil:
    """ IPython extensios (ipy_* etc.) management utilities """

    def describe(self):
        for n,mod in self._active():
            doc = inspect.getdoc(mod)
            if doc:
                print '== %s ==' % n
                print indent(doc)


    def ls(self):
        """ Show list of installed extensions. """
        for n,m in self._active():
            print '%-20s %s' % (n,m.__file__.replace('\\','/'))
    def _active(self):
        act = []
        for mname,m in sys.modules.items():
            o = getattr(m, 'ip', None)
            if isinstance(o, InteractiveShell):
                act.append((mname,m))
        act.sort()
        return act

extutil = ExtUtil()
ip.push('extutil')
