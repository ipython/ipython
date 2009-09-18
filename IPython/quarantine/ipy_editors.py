""" 'editor' hooks for common editors that work well with ipython

They should honor the line number argument, at least.

Contributions are *very* welcome.
"""

from IPython.core import ipapi
from IPython.core.error import TryNext
ip = ipapi.get()

from IPython.external.Itpl import itplns
import os

def install_editor(run_template, wait = False):
    """ Gets a template in format "myeditor bah bah $file bah bah $line"
    
    $file will be replaced by file name, $line by line number (or 0).
    Installs the editor that is called by IPython, instead of the default
    notepad or vi.
    
    If wait is true, wait until the user presses enter before returning,
    to facilitate non-blocking editors that exit immediately after
    the call.
    """
    
    def call_editor(self, file, line=0):
        if line is None:
            line = 0
        cmd = itplns(run_template, locals())
        print ">",cmd
        if os.system(cmd) != 0:
            raise TryNext()
        if wait:
            raw_input("Press Enter when done editing:")

    ip.set_hook('editor',call_editor)


# in these, exe is always the path/name of the executable. Useful
# if you don't have the editor directory in your path

def komodo(exe = 'komodo'):
    """ Activestate Komodo [Edit] """
    install_editor(exe + ' -l $line "$file"', wait = True)

def scite(exe = "scite"):
    """ SciTE or Sc1 """
    install_editor(exe + ' "$file" -goto:$line')

def notepadplusplus(exe = 'notepad++'):
    """ Notepad++ http://notepad-plus.sourceforge.net """
    install_editor(exe + ' -n$line "$file"')
    
def jed(exe = 'jed'):
    """ JED, the lightweight emacsish editor """
    install_editor(exe + ' +$line "$file"')

def idle(exe = None):
    """ Idle, the editor bundled with python
    
    Should be pretty smart about finding the executable.
    """
    if exe is None:
        import idlelib
        p = os.path.dirname(idlelib.__file__)
        exe = p + '/idle.py'
    install_editor(exe + ' "$file"')

def mate(exe = 'mate'):
    """ TextMate, the missing editor"""
    install_editor(exe + ' -w -l $line "$file"')

# these are untested, report any problems

def emacs(exe = 'emacs'):
    install_editor(exe + ' +$line "$file"')

def gnuclient(exe= 'gnuclient'):
    install_editor(exe + ' -nw +$line "$file"')

def crimson_editor(exe = 'cedt.exe'):
    install_editor(exe + ' /L:$line "$file"')
    
def kate(exe = 'kate'):
    install_editor(exe + ' -u -l $line "$file"')
    
   
    