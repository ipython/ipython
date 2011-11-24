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

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import sys
import tempfile

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
        if isinstance(lines, basestring):
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


class IOTerm:
    """ Term holds the file or file-like objects for handling I/O operations.

    These are normally just sys.stdin, sys.stdout and sys.stderr but for
    Windows they can can replaced to allow editing the strings before they are
    displayed."""

    # In the future, having IPython channel all its I/O operations through
    # this class will make it easier to embed it into other environments which
    # are not a normal terminal (such as a GUI-based shell)
    def __init__(self, stdin=None, stdout=None, stderr=None):
        self.stdin  = IOStream(stdin, sys.stdin)
        self.stdout = IOStream(stdout, sys.stdout)
        self.stderr = IOStream(stderr, sys.stderr)

# setup stdin/stdout/stderr to sys.stdin/sys.stdout/sys.stderr
stdin = IOStream(sys.stdin)
stdout = IOStream(sys.stdout)
stderr = IOStream(sys.stderr)


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


def file_read(filename):
    """Read a file and close it.  Returns the file source."""
    fobj = open(filename,'r');
    source = fobj.read();
    fobj.close()
    return source


def file_readlines(filename):
    """Read a file and close it.  Returns the file source using readlines()."""
    fobj = open(filename,'r');
    lines = fobj.readlines();
    fobj.close()
    return lines


def raw_input_multi(header='', ps1='==> ', ps2='..> ',terminate_str = '.'):
    """Take multiple lines of input.

    A list with each line of input as a separate element is returned when a
    termination string is entered (defaults to a single '.'). Input can also
    terminate via EOF (^D in Unix, ^Z-RET in Windows).

    Lines of input which end in \\ are joined into single entries (and a
    secondary continuation prompt is issued as long as the user terminates
    lines with \\). This allows entering very long strings which are still
    meant to be treated as single entities.
    """

    try:
        if header:
            header += '\n'
        lines = [raw_input(header + ps1)]
    except EOFError:
        return []
    terminate = [terminate_str]
    try:
        while lines[-1:] != terminate:
            new_line = raw_input(ps1)
            while new_line.endswith('\\'):
                new_line = new_line[:-1] + raw_input(ps2)
            lines.append(new_line)

        return lines[:-1]  # don't return the termination command
    except EOFError:
        print()
        return lines


def raw_input_ext(prompt='',  ps2='... '):
    """Similar to raw_input(), but accepts extended lines if input ends with \\."""

    line = raw_input(prompt)
    while line.endswith('\\'):
        line = line[:-1] + raw_input(ps2)
    return line


def ask_yes_no(prompt,default=None):
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. Otherwise the question is repeated until an answer is given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""

    answers = {'y':True,'n':False,'yes':True,'no':False}
    ans = None
    while ans not in answers.keys():
        try:
            ans = raw_input(prompt+' ').lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            pass
        except EOFError:
            if default in answers.keys():
                ans = default
                print()
            else:
                raise

    return answers[ans]


class NLprinter:
    """Print an arbitrarily nested list, indicating index numbers.

    An instance of this class called nlprint is available and callable as a
    function.

    nlprint(list,indent=' ',sep=': ') -> prints indenting each level by 'indent'
    and using 'sep' to separate the index from the value. """

    def __init__(self):
        self.depth = 0

    def __call__(self,lst,pos='',**kw):
        """Prints the nested list numbering levels."""
        kw.setdefault('indent',' ')
        kw.setdefault('sep',': ')
        kw.setdefault('start',0)
        kw.setdefault('stop',len(lst))
        # we need to remove start and stop from kw so they don't propagate
        # into a recursive call for a nested list.
        start = kw['start']; del kw['start']
        stop = kw['stop']; del kw['stop']
        if self.depth == 0 and 'header' in kw.keys():
            print(kw['header'])

        for idx in range(start,stop):
            elem = lst[idx]
            newpos = pos + str(idx)
            if type(elem)==type([]):
                self.depth += 1
                self.__call__(elem, newpos+",", **kw)
                self.depth -= 1
            else:
                print(kw['indent']*self.depth + newpos + kw["sep"] + repr(elem))

nlprint = NLprinter()


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
