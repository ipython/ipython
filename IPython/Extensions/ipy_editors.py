""" 'editor' hooks for common editors that work well with ipython

They should honor the line number argument, at least.

Contributions are *very* welcome.
"""

import IPython.ipapi
ip = IPython.ipapi.get()

from IPython.Itpl import itplns
import os

def install_editor(run_template):
    def call_editor(self, file, line):
        if line is None:
            line = 0
        cmd = itplns(run_template, locals())
        print ">",cmd
        os.system(cmd)

    ip.set_hook('editor',call_editor)

def komodo(exe = 'komodo'):
    """ Warning - komodo does not block """
    install_editor(exe + ' -l $line "$file"')

def scite(exe = "scite"):
    """ Exe is the executable name of your scite.
    """
    install_editor(exe + ' "$file" -goto:$line')