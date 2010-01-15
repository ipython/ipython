"""Base utilities support for IPython.

Warning: this is a module that other utilities modules will import from, so it
can ONLY depend on the standard library, and NOTHING ELSE.  In particular, this
module can NOT import anything from IPython, or circular dependencies will arise.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import subprocess

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def getoutputerror(cmd,verbose=0,debug=0,header='',split=0):
    """Return (standard output,standard error) of executing cmd in a shell.

    Accepts the same arguments as system(), plus:

    - split(0): if true, each of stdout/err is returned as a list split on
    newlines.

    Note: a stateful version of this function is available through the
    SystemExec class."""

    if verbose or debug: print header+cmd
    if not cmd:
        if split:
            return [],[]
        else:
            return '',''
    if not debug:
        p = subprocess.Popen(cmd, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        pin, pout, perr = (p.stdin, p.stdout, p.stderr)

        tout = pout.read().rstrip()
        terr = perr.read().rstrip()
        pin.close()
        pout.close()
        perr.close()
        if split:
            return tout.split('\n'),terr.split('\n')
        else:
            return tout,terr
