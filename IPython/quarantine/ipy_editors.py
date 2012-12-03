""" 'editor' hooks for common editors that work well with ipython

They should honor the line number argument, at least.

Contributions are *very* welcome.
"""

from IPython.core.error import TryNext
from string import Template
import os


def install_editor(run_template, wait=False):
    """Installs the editor that is called by IPython for the %edit magic.

    This overrides the default editor, which is generally set by your EDITOR
    environment variable or is notepad (windows) or vi (linux). By supplying a
    template string `run_template`, you can control how the editor is invoked
    by IPython -- (e.g. the format in which it accepts command line options)

    Parameters
    ----------
    run_template : basestring
        run_template acts as a template for how your editor is invoked by
        the shell. It should contain '$file', which will be replaced on
        invokation with the file name, and '$line$', $line by line number
        (or 0) to invoke the file with.
    wait : bool
        If `wait` is true, wait until the user presses enter before returning,
        to facilitate non-blocking editors that exit immediately after
        the call.
    """

    for substitution in ['$file', '$line']:
        if not substitution in run_template:
            raise ValueError(('run_template should contain %s'
            ' for string substitution. You supplied "%s"' % (substitution,
                run_template)))

    template = Template(run_template)

    def call_editor(self, file, line=0):
        if line is None:
            line = 0
        cmd = template.substitute(file=file, line=line)
        print ">", cmd
        if os.system(cmd) != 0:
            raise TryNext()
        if wait:
            raw_input("Press Enter when done editing:")

    get_ipython().set_hook('editor', call_editor)


# in these, exe is always the path/name of the executable. Useful
# if you don't have the editor directory in your path


def komodo(exe='komodo'):
    """ Activestate Komodo [Edit] """
    install_editor(exe + ' -l $line "$file"', wait=True)


def scite(exe="scite"):
    """ SciTE or Sc1 """
    install_editor(exe + ' "$file" -goto:$line')


def notepadplusplus(exe='notepad++'):
    """ Notepad++ http://notepad-plus.sourceforge.net """
    install_editor(exe + ' -n$line "$file"')


def jed(exe='jed'):
    """ JED, the lightweight emacsish editor """
    install_editor(exe + ' +$line "$file"')


def idle(exe=None):
    """ Idle, the editor bundled with python

    Should be pretty smart about finding the executable.
    """
    if exe is None:
        import idlelib
        p = os.path.dirname(idlelib.__file__)
        exe = os.path.join(p, 'idle.py')
    install_editor(exe + ' "$file"')


def mate(exe='mate'):
    """ TextMate, the missing editor"""
    # wait=True is not required since we're using the -w flag to mate
    install_editor(exe + ' -w -l $line "$file"')


# ##########################################
# these are untested, report any problems
# ##########################################


def emacs(exe='emacs'):
    install_editor(exe + ' +$line "$file"')


def gnuclient(exe='gnuclient'):
    install_editor(exe + ' -nw +$line "$file"')


def crimson_editor(exe='cedt.exe'):
    install_editor(exe + ' /L:$line "$file"')


def kate(exe='kate'):
    install_editor(exe + ' -u -l $line "$file"')
