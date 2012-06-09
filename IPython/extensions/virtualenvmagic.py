# -*- coding: utf-8 -*-
"""
Virtualenv magic
Requires virtualenv and virtualenv Wrapper
Author: Flávio Codeço Coelho - @fccoelho
Thanks to @turicas for helpful tips
"""
import sys
import os
import shlex
from subprocess import Popen, PIPE
from IPython.core.magic import cell_magic


@cell_magic('virtualenv')
def virtualenv(line, cell):
    """
    This magic enables the execution of code in a cell on a
    pre-existing virtual env. It Requires Virtualenv and VirtualenvWrapper
    to be installed in the system.
    The virtual env to be used must be created in advance.

    Usage
    =====
    To activate this magic just write at the top of the cell:

        %%virtualenv my_env
        import sys
        print sys.version


    """
    if not os.path.exists(os.environ['WORKON_HOME'] + '/' + line):
        print >> sys.stderr, "Environment {} does not exist.".format(line)
        return
    env_activate_cmd = 'bash -c "source {}/{}/bin/activate && python -"'\
    .format(os.environ['WORKON_HOME'], line)
    cmd = shlex.split(env_activate_cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
    out, err = p.communicate(cell)
    p.wait()
    if err:
        print >> sys.stderr, err
    return out

_loaded = False


def load_ipython_extension(ip):
    """
    Load the extension in IPython.
    """
    global _loaded
    if not _loaded:
        if 'WORKON_HOME' in os.environ:
            ip.register_magic_function(virtualenv, 'cell')
            _loaded = True
        else:
            print >> sys.stderr, "You must have Virtualenv and \
            VirtualenvWrapper installed."
