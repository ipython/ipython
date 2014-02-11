# encoding: utf-8
"""
IO related utilities.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
from __future__ import print_function
from __future__ import absolute_import

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import codecs
import os
import sys
import tempfile
from .capture import CapturedIO, capture_output
from .py3compat import string_types, input, PY3

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


class IOStream:

    def __init__(self,stream, fallback=None):
        if not hasattr(stream,'write') or not hasattr(stream,'flush'):
            if fallback is not None:
                stream = fallback
            else:
                raise ValueError("fallback required, but not specified")
        self.stream = stream
        self._swrite = stream.write

        # clone all methods not overridden:
        def clone(meth):
            return not hasattr(self, meth) and not meth.startswith('_')
        for meth in filter(clone, dir(stream)):
            setattr(self, meth, getattr(stream, meth))

    def __repr__(self):
        cls = self.__class__
        tpl = '{mod}.{cls}({args})'
        return tpl.format(mod=cls.__module__, cls=cls.__name__, args=self.stream)

    def write(self,data):
        try:
            self._swrite(data)
        except:
            try:
                # print handles some unicode issues which may trip a plain
                # write() call.  Emulate write() by using an empty end
                # argument.
                print(data, end='', file=self.stream)
            except:
                # if we get here, something is seriously broken.
                print('ERROR - failed to write data to stream:', self.stream,
                      file=sys.stderr)

    def writelines(self, lines):
        if isinstance(lines, string_types):
            lines = [lines]
        for line in lines:
            self.write(line)

    # This class used to have a writeln method, but regular files and streams
    # in Python don't have this method. We need to keep this completely
    # compatible so we removed it.

    @property
    def closed(self):
        return self.stream.closed

    def close(self):
        pass

# setup stdin/stdout/stderr to sys.stdin/sys.stdout/sys.stderr
devnull = open(os.devnull, 'w') 
stdin = IOStream(sys.stdin, fallback=devnull)
stdout = IOStream(sys.stdout, fallback=devnull)
stderr = IOStream(sys.stderr, fallback=devnull)

class IOTerm:
    """ Term holds the file or file-like objects for handling I/O operations.

    These are normally just sys.stdin, sys.stdout and sys.stderr but for
    Windows they can can replaced to allow editing the strings before they are
    displayed."""

    # In the future, having IPython channel all its I/O operations through
    # this class will make it easier to embed it into other environments which
    # are not a normal terminal (such as a GUI-based shell)
    def __init__(self, stdin=None, stdout=None, stderr=None):
        mymodule = sys.modules[__name__]
        self.stdin  = IOStream(stdin, mymodule.stdin)
        self.stdout = IOStream(stdout, mymodule.stdout)
        self.stderr = IOStream(stderr, mymodule.stderr)


class Tee(object):
    """A class to duplicate an output stream to stdout/err.

    This works in a manner very similar to the Unix 'tee' command.

    When the object is closed or deleted, it closes the original file given to
    it for duplication.
    """
    # Inspired by:
    # http://mail.python.org/pipermail/python-list/2007-May/442737.html

    def __init__(self, file_or_name, mode="w", channel='stdout'):
        """Construct a new Tee object.

        Parameters
        ----------
        file_or_name : filename or open filehandle (writable)
          File that will be duplicated

        mode : optional, valid mode for open().
          If a filename was give, open with this mode.

        channel : str, one of ['stdout', 'stderr']
        """
        if channel not in ['stdout', 'stderr']:
            raise ValueError('Invalid channel spec %s' % channel)

        if hasattr(file_or_name, 'write') and hasattr(file_or_name, 'seek'):
            self.file = file_or_name
        else:
            self.file = open(file_or_name, mode)
        self.channel = channel
        self.ostream = getattr(sys, channel)
        setattr(sys, channel, self)
        self._closed = False

    def close(self):
        """Close the file and restore the channel."""
        self.flush()
        setattr(sys, self.channel, self.ostream)
        self.file.close()
        self._closed = True

    def write(self, data):
        """Write data to both channels."""
        self.file.write(data)
        self.ostream.write(data)
        self.ostream.flush()

    def flush(self):
        """Flush both channels."""
        self.file.flush()
        self.ostream.flush()

    def __del__(self):
        if not self._closed:
            self.close()


def ask_yes_no(prompt, default=None, interrupt=None):
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. If interrupt is given (one of 'y','n'), it is used if the user
    presses Ctrl-C. Otherwise the question is repeated until an answer is
    given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""

    answers = {'y':True,'n':False,'yes':True,'no':False}
    ans = None
    while ans not in answers.keys():
        try:
            ans = input(prompt+' ').lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            if interrupt:
                ans = interrupt
        except EOFError:
            if default in answers.keys():
                ans = default
                print()
            else:
                raise

    return answers[ans]


def temp_pyfile(src, ext='.py'):
    """Make a temporary python file, return filename and filehandle.

    Parameters
    ----------
    src : string or list of strings (no need for ending newlines if list)
      Source code to be written to the file.

    ext : optional, string
      Extension for the generated file.

    Returns
    -------
    (filename, open filehandle)
      It is the caller's responsibility to close the open file and unlink it.
    """
    fname = tempfile.mkstemp(ext)[1]
    f = open(fname,'w')
    f.write(src)
    f.flush()
    return fname, f


def raw_print(*args, **kw):
    """Raw print to sys.__stdout__, otherwise identical interface to print()."""

    print(*args, sep=kw.get('sep', ' '), end=kw.get('end', '\n'),
          file=sys.__stdout__)
    sys.__stdout__.flush()


def raw_print_err(*args, **kw):
    """Raw print to sys.__stderr__, otherwise identical interface to print()."""

    print(*args, sep=kw.get('sep', ' '), end=kw.get('end', '\n'),
          file=sys.__stderr__)
    sys.__stderr__.flush()


# Short aliases for quick debugging, do NOT use these in production code.
rprint = raw_print
rprinte = raw_print_err

def unicode_std_stream(stream='stdout'):
    u"""Get a wrapper to write unicode to stdout/stderr as UTF-8.

    This ignores environment variables and default encodings, to reliably write
    unicode to stdout or stderr.

    ::

        unicode_std_stream().write(u'ł@e¶ŧ←')
    """
    assert stream in ('stdout', 'stderr')
    stream  = getattr(sys, stream)
    if PY3:
        try:
            stream_b = stream.buffer
        except AttributeError:
            # sys.stdout has been replaced - use it directly
            return stream
    else:
        stream_b = stream

    return codecs.getwriter('utf-8')(stream_b)
