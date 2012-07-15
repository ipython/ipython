""" Advanced signal (e.g. ctrl+C) handling for IPython

So far, this only ignores ctrl + C in IPython file a subprocess
is executing, to get closer to how a "proper" shell behaves.

Other signal processing may be implemented later on.

If _ip.options.verbose is true, show exit status if nonzero

"""

import signal,os,sys
from IPython.core import ipapi
import subprocess

ip = ipapi.get()

def new_ipsystem_posix(cmd):
    """ ctrl+c ignoring replacement for system() command in iplib.

    Ignore ctrl + c in IPython process during the command execution.
    The subprocess will still get the ctrl + c signal.

    posix implementation
    """

    p =  subprocess.Popen(cmd, shell = True)

    old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    pid,status = os.waitpid(p.pid,0)
    signal.signal(signal.SIGINT, old_handler)
    if status and ip.options.verbose:
        print "[exit status: %d]" % status

def new_ipsystem_win32(cmd):
    """ ctrl+c ignoring replacement for system() command in iplib.

    Ignore ctrl + c in IPython process during the command execution.
    The subprocess will still get the ctrl + c signal.

    win32 implementation
    """
    old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    status = os.system(cmd)
    signal.signal(signal.SIGINT, old_handler)
    if status and ip.options.verbose:
        print "[exit status: %d]" % status


def init():
    o = ip.options
    try:
        o.verbose
    except AttributeError:
        o.allow_new_attr (True )
        o.verbose = 0

    ip.system = (sys.platform == 'win32' and new_ipsystem_win32 or
                    new_ipsystem_posix)

init()
