""" 'editor' hooks for common editors that work well with ipython

They should honor the line number argument, at least.

Contributions are *very* welcome.
"""

import IPython.ipapi
ip = IPython.ipapi.get()

from IPython.Itpl import itplns
import os

def install_editor(run_template, wait = False):
    """ Gets a template in format "myeditor bah bah $file bah bah $line
    
    Installs the editor that is called by IPython, instead of the default
    notepad or vi.
    """
    
    def call_editor(self, file, line):
        if line is None:
            line = 0
        cmd = itplns(run_template, locals())
        print ">",cmd
        os.system(cmd)
        if wait:
            raw_input("Press Enter when done editing:")

    ip.set_hook('editor',call_editor)

def komodo(exe = 'komodo'):
    """ Activestate Komodo [Edit]
    
    Warning - komodo does not block, so can't be used for plain %edit
    
    """
    install_editor(exe + ' -l $line "$file"', wait = True)

def scite(exe = "scite"):
    """ Exe is the executable name of your scite.
    """
    install_editor(exe + ' "$file" -goto:$line')