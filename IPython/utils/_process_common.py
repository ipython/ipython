"""Common utilities for the various process_* implementations.

This file is only meant to be imported by the platform-specific implementations
of subprocess utilities, and it contains tools that are common to all of them.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import subprocess
import sys

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------

def read_no_interrupt(p):
    """Read from a pipe ignoring EINTR errors.

    This is necessary because when reading from pipes with GUI event loops
    running in the background, often interrupts are raised that stop the
    command from completing."""
    import errno

    try:
        return p.read()
    except IOError, err:
        if err.errno != errno.EINTR:
            raise


def process_handler(cmd, callback, stderr=subprocess.PIPE):
    """Open a command in a shell subprocess and execute a callback.

    This function provides common scaffolding for creating subprocess.Popen()
    calls.  It creates a Popen object and then calls the callback with it.

    Parameters
    ----------
    cmd : str
      A string to be executed with the underlying system shell (by calling
    :func:`Popen` with ``shell=True``.

    callback : callable
      A one-argument function that will be called with the Popen object.

    stderr : file descriptor number, optional
      By default this is set to ``subprocess.PIPE``, but you can also pass the
      value ``subprocess.STDOUT`` to force the subprocess' stderr to go into
      the same file descriptor as its stdout.  This is useful to read stdout
      and stderr combined in the order they are generated.

    Returns
    -------
    The return value of the provided callback is returned.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    close_fds = False if sys.platform=='win32' else True
    p = subprocess.Popen(cmd, shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=stderr,
                         close_fds=close_fds)

    try:
        out = callback(p)
    except KeyboardInterrupt:
        print('^C')
        sys.stdout.flush()
        sys.stderr.flush()
        out = None
    finally:
        # Make really sure that we don't leave processes behind, in case the
        # call above raises an exception
        # We start by assuming the subprocess finished (to avoid NameErrors
        # later depending on the path taken)
        if p.returncode is None:
            try:
                p.terminate()
                p.poll()
            except OSError:
                pass
        # One last try on our way out
        if p.returncode is None:
            try:
                p.kill()
            except OSError:
                pass

    return out


def getoutputerror(cmd):
    """Return (standard output, standard error) of executing cmd in a shell.

    Accepts the same arguments as os.system().

    Parameters
    ----------
    cmd : str
      A command to be executed in the system shell.

    Returns
    -------
    stdout : str
    stderr : str
    """

    out_err = process_handler(cmd, lambda p: p.communicate())
    if out_err is None:
        out_err = '', ''
    return out_err
