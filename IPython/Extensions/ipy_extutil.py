""" IPython extension management tools.

After installation, you'll have the 'extutil' object in your namespace.
to.
"""

# for the purposes of this module, every module that has the name 'ip' globally
# installed as below is an IPython extension

import IPython.ipapi
ip = IPython.ipapi.get()

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
            if isinstance(o, IPython.ipapi.IPApi):
                act.append((mname,m))
        act.sort()                
        return act

extutil = ExtUtil()                
ip.to_user_ns('extutil')
