"""Common utilities for the various process_* implementations.

This file is only meant to be imported by the platform-specific implementations
of subprocess utilities, and it contains tools that are common to all of them.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import subprocess
import shlex
import sys

from IPython.utils import py3compat

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
    # On win32, close_fds can't be true when using pipes for stdin/out/err
    close_fds = sys.platform != 'win32'
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


def getoutput(cmd):
    """Return standard output of executing cmd in a shell.

    Accepts the same arguments as os.system().

    Parameters
    ----------
    cmd : str
      A command to be executed in the system shell.

    Returns
    -------
    stdout : str
    """

    out = process_handler(cmd, lambda p: p.communicate()[0], subprocess.STDOUT)
    if out is None:
        return ''
    return py3compat.bytes_to_str(out)


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
        return '', ''
    out, err = out_err
    return py3compat.bytes_to_str(out), py3compat.bytes_to_str(err)


def arg_split(s, posix=False, strict=True):
    """Split a command line's arguments in a shell-like manner.

    This is a modified version of the standard library's shlex.split()
    function, but with a default of posix=False for splitting, so that quotes
    in inputs are respected.

    if strict=False, then any errors shlex.split would raise will result in the
    unparsed remainder being the last element of the list, rather than raising.
    This is because we sometimes use arg_split to parse things other than
    command-line args.
    """

    # Unfortunately, python's shlex module is buggy with unicode input:
    # http://bugs.python.org/issue1170
    # At least encoding the input when it's unicode seems to help, but there
    # may be more problems lurking.  Apparently this is fixed in python3.
    is_unicode = False
    if (not py3compat.PY3) and isinstance(s, unicode):
        is_unicode = True
        s = s.encode('utf-8')
    lex = shlex.shlex(s, posix=posix)
    lex.whitespace_split = True
    # Extract tokens, ensuring that things like leaving open quotes
    # does not cause this to raise.  This is important, because we
    # sometimes pass Python source through this (e.g. %timeit f(" ")),
    # and it shouldn't raise an exception.
    # It may be a bad idea to parse things that are not command-line args
    # through this function, but we do, so let's be safe about it.
    lex.commenters='' #fix for GH-1269
    tokens = []
    while True:
        try:
            tokens.append(lex.next())
        except StopIteration:
            break
        except ValueError:
            if strict:
                raise
            # couldn't parse, get remaining blob as last token
            tokens.append(lex.token)
            break
    
    if is_unicode:
        # Convert the tokens back to unicode.
        tokens = [x.decode('utf-8') for x in tokens]
    return tokens
