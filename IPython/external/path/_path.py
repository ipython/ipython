#
# Copyright (c) 2010 Mikhail Gusarov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

""" path.py - An object representing a path to a file or directory.

Original author:
 Jason Orendorff <jason.orendorff\x40gmail\x2ecom>

Current maintainer:
 Jason R. Coombs <jaraco@jaraco.com>

Contributors:
 Mikhail Gusarov <dottedmag@dottedmag.net>
 Marc Abramowitz <marc@marc-abramowitz.com>
 Jason R. Coombs <jaraco@jaraco.com>
 Jason Chu <jchu@xentac.net>
 Vojislav Stojkovic <vstojkovic@syntertainment.com>

Example::

    from path import path
    d = path('/home/guido/bin')
    for f in d.files('*.py'):
        f.chmod(0755)

path.py requires Python 2.5 or later.
"""

from __future__ import with_statement

import sys
import warnings
import os
import fnmatch
import glob
import shutil
import codecs
import hashlib
import errno
import tempfile
import functools
import operator
import re

try:
    import win32security
except ImportError:
    pass

try:
    import pwd
except ImportError:
    pass

################################
# Monkey patchy python 3 support
try:
    basestring
except NameError:
    basestring = str

try:
    unicode
except NameError:
    unicode = str

try:
    getcwdu = os.getcwdu
except AttributeError:
    getcwdu = os.getcwd

if sys.version < '3':
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x

o777 = 511
o766 = 502
o666 = 438
o554 = 364
################################

__version__ = '4.3'
__all__ = ['path']


class TreeWalkWarning(Warning):
    pass


def simple_cache(func):
    """
    Save results for the 'using_module' classmethod.
    When Python 3.2 is available, use functools.lru_cache instead.
    """
    saved_results = {}

    def wrapper(cls, module):
        if module in saved_results:
            return saved_results[module]
        saved_results[module] = func(cls, module)
        return saved_results[module]
    return wrapper


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class multimethod(object):
    """
    Acts like a classmethod when invoked from the class and like an
    instancemethod when invoked from the instance.
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return (
            functools.partial(self.func, owner) if instance is None
            else functools.partial(self.func, owner, instance)
        )


class path(unicode):
    """ Represents a filesystem path.

    For documentation on individual methods, consult their
    counterparts in os.path.
    """

    module = os.path
    "The path module to use for path operations."

    def __init__(self, other=''):
        if other is None:
            raise TypeError("Invalid initial value for path: None")

    @classmethod
    @simple_cache
    def using_module(cls, module):
        subclass_name = cls.__name__ + '_' + module.__name__
        bases = (cls,)
        ns = {'module': module}
        return type(subclass_name, bases, ns)

    @ClassProperty
    @classmethod
    def _next_class(cls):
        """
        What class should be used to construct new instances from this class
        """
        return cls

    # --- Special Python methods.

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super(path, self).__repr__())

    # Adding a path and a string yields a path.
    def __add__(self, more):
        try:
            return self._next_class(super(path, self).__add__(more))
        except TypeError:  # Python bug
            return NotImplemented

    def __radd__(self, other):
        if not isinstance(other, basestring):
            return NotImplemented
        return self._next_class(other.__add__(self))

    # The / operator joins paths.
    def __div__(self, rel):
        """ fp.__div__(rel) == fp / rel == fp.joinpath(rel)

        Join two path components, adding a separator character if
        needed.
        """
        return self._next_class(self.module.join(self, rel))

    # Make the / operator work even when true division is enabled.
    __truediv__ = __div__

    def __enter__(self):
        self._old_dir = self.getcwd()
        os.chdir(self)
        return self

    def __exit__(self, *_):
        os.chdir(self._old_dir)

    @classmethod
    def getcwd(cls):
        """ Return the current working directory as a path object. """
        return cls(getcwdu())

    #
    # --- Operations on path strings.

    def abspath(self):
        return self._next_class(self.module.abspath(self))

    def normcase(self):
        return self._next_class(self.module.normcase(self))

    def normpath(self):
        return self._next_class(self.module.normpath(self))

    def realpath(self):
        return self._next_class(self.module.realpath(self))

    def expanduser(self):
        return self._next_class(self.module.expanduser(self))

    def expandvars(self):
        return self._next_class(self.module.expandvars(self))

    def dirname(self):
        return self._next_class(self.module.dirname(self))

    def basename(self):
        return self._next_class(self.module.basename(self))

    def expand(self):
        """ Clean up a filename by calling expandvars(),
        expanduser(), and normpath() on it.

        This is commonly everything needed to clean up a filename
        read from a configuration file, for example.
        """
        return self.expandvars().expanduser().normpath()

    @property
    def namebase(self):
        """ The same as path.name, but with one file extension stripped off.

        For example, path('/home/guido/python.tar.gz').name == 'python.tar.gz',
        but          path('/home/guido/python.tar.gz').namebase == 'python.tar'
        """
        base, ext = self.module.splitext(self.name)
        return base

    @property
    def ext(self):
        """ The file extension, for example '.py'. """
        f, ext = self.module.splitext(self)
        return ext

    @property
    def drive(self):
        """ The drive specifier, for example 'C:'.
        This is always empty on systems that don't use drive specifiers.
        """
        drive, r = self.module.splitdrive(self)
        return self._next_class(drive)

    parent = property(
        dirname, None, None,
        """ This path's parent directory, as a new path object.

        For example,
        path('/usr/local/lib/libpython.so').parent == path('/usr/local/lib')
        """)

    name = property(
        basename, None, None,
        """ The name of this file or directory without the full path.

        For example, path('/usr/local/lib/libpython.so').name == 'libpython.so'
        """)

    def splitpath(self):
        """ p.splitpath() -> Return (p.parent, p.name). """
        parent, child = self.module.split(self)
        return self._next_class(parent), child

    def splitdrive(self):
        """ p.splitdrive() -> Return (p.drive, <the rest of p>).

        Split the drive specifier from this path.  If there is
        no drive specifier, p.drive is empty, so the return value
        is simply (path(''), p).  This is always the case on Unix.
        """
        drive, rel = self.module.splitdrive(self)
        return self._next_class(drive), rel

    def splitext(self):
        """ p.splitext() -> Return (p.stripext(), p.ext).

        Split the filename extension from this path and return
        the two parts.  Either part may be empty.

        The extension is everything from '.' to the end of the
        last path segment.  This has the property that if
        (a, b) == p.splitext(), then a + b == p.
        """
        filename, ext = self.module.splitext(self)
        return self._next_class(filename), ext

    def stripext(self):
        """ p.stripext() -> Remove one file extension from the path.

        For example, path('/home/guido/python.tar.gz').stripext()
        returns path('/home/guido/python.tar').
        """
        return self.splitext()[0]

    def splitunc(self):
        unc, rest = self.module.splitunc(self)
        return self._next_class(unc), rest

    @property
    def uncshare(self):
        """
        The UNC mount point for this path.
        This is empty for paths on local drives.
        """
        unc, r = self.module.splitunc(self)
        return self._next_class(unc)

    @multimethod
    def joinpath(cls, first, *others):
        """
        Join first to zero or more path components, adding a separator
        character (first.module.sep) if needed.  Returns a new instance of
        first._next_class.
        """
        if not isinstance(first, cls):
            first = cls(first)
        return first._next_class(first.module.join(first, *others))

    def splitall(self):
        r""" Return a list of the path components in this path.

        The first item in the list will be a path.  Its value will be
        either os.curdir, os.pardir, empty, or the root directory of
        this path (for example, ``'/'`` or ``'C:\\'``).  The other items in
        the list will be strings.

        ``path.path.joinpath(*result)`` will yield the original path.
        """
        parts = []
        loc = self
        while loc != os.curdir and loc != os.pardir:
            prev = loc
            loc, child = prev.splitpath()
            if loc == prev:
                break
            parts.append(child)
        parts.append(loc)
        parts.reverse()
        return parts

    def relpath(self, start='.'):
        """ Return this path as a relative path,
        based from start, which defaults to the current working directory.
        """
        cwd = self._next_class(start)
        return cwd.relpathto(self)

    def relpathto(self, dest):
        """ Return a relative path from self to dest.

        If there is no relative path from self to dest, for example if
        they reside on different drives in Windows, then this returns
        dest.abspath().
        """
        origin = self.abspath()
        dest = self._next_class(dest).abspath()

        orig_list = origin.normcase().splitall()
        # Don't normcase dest!  We want to preserve the case.
        dest_list = dest.splitall()

        if orig_list[0] != self.module.normcase(dest_list[0]):
            # Can't get here from there.
            return dest

        # Find the location where the two paths start to differ.
        i = 0
        for start_seg, dest_seg in zip(orig_list, dest_list):
            if start_seg != self.module.normcase(dest_seg):
                break
            i += 1

        # Now i is the point where the two paths diverge.
        # Need a certain number of "os.pardir"s to work up
        # from the origin to the point of divergence.
        segments = [os.pardir] * (len(orig_list) - i)
        # Need to add the diverging part of dest_list.
        segments += dest_list[i:]
        if len(segments) == 0:
            # If they happen to be identical, use os.curdir.
            relpath = os.curdir
        else:
            relpath = self.module.join(*segments)
        return self._next_class(relpath)

    # --- Listing, searching, walking, and matching

    def listdir(self, pattern=None):
        """ D.listdir() -> List of items in this directory.

        Use D.files() or D.dirs() instead if you want a listing
        of just files or just subdirectories.

        The elements of the list are path objects.

        With the optional 'pattern' argument, this only lists
        items whose names match the given pattern.
        """
        names = os.listdir(self)
        if pattern is not None:
            names = fnmatch.filter(names, pattern)
        return [self / child for child in names]

    def dirs(self, pattern=None):
        """ D.dirs() -> List of this directory's subdirectories.

        The elements of the list are path objects.
        This does not walk recursively into subdirectories
        (but see path.walkdirs).

        With the optional 'pattern' argument, this only lists
        directories whose names match the given pattern.  For
        example, ``d.dirs('build-*')``.
        """
        return [p for p in self.listdir(pattern) if p.isdir()]

    def files(self, pattern=None):
        """ D.files() -> List of the files in this directory.

        The elements of the list are path objects.
        This does not walk into subdirectories (see path.walkfiles).

        With the optional 'pattern' argument, this only lists files
        whose names match the given pattern.  For example,
        ``d.files('*.pyc')``.
        """

        return [p for p in self.listdir(pattern) if p.isfile()]

    def walk(self, pattern=None, errors='strict'):
        """ D.walk() -> iterator over files and subdirs, recursively.

        The iterator yields path objects naming each child item of
        this directory and its descendants.  This requires that
        D.isdir().

        This performs a depth-first traversal of the directory tree.
        Each directory is returned just before all its children.

        The errors= keyword argument controls behavior when an
        error occurs.  The default is 'strict', which causes an
        exception.  The other allowed values are 'warn', which
        reports the error via warnings.warn(), and 'ignore'.
        """
        if errors not in ('strict', 'warn', 'ignore'):
            raise ValueError("invalid errors parameter")

        try:
            childList = self.listdir()
        except Exception:
            if errors == 'ignore':
                return
            elif errors == 'warn':
                warnings.warn(
                    "Unable to list directory '%s': %s"
                    % (self, sys.exc_info()[1]),
                    TreeWalkWarning)
                return
            else:
                raise

        for child in childList:
            if pattern is None or child.fnmatch(pattern):
                yield child
            try:
                isdir = child.isdir()
            except Exception:
                if errors == 'ignore':
                    isdir = False
                elif errors == 'warn':
                    warnings.warn(
                        "Unable to access '%s': %s"
                        % (child, sys.exc_info()[1]),
                        TreeWalkWarning)
                    isdir = False
                else:
                    raise

            if isdir:
                for item in child.walk(pattern, errors):
                    yield item

    def walkdirs(self, pattern=None, errors='strict'):
        """ D.walkdirs() -> iterator over subdirs, recursively.

        With the optional 'pattern' argument, this yields only
        directories whose names match the given pattern.  For
        example, ``mydir.walkdirs('*test')`` yields only directories
        with names ending in 'test'.

        The errors= keyword argument controls behavior when an
        error occurs.  The default is 'strict', which causes an
        exception.  The other allowed values are 'warn', which
        reports the error via warnings.warn(), and 'ignore'.
        """
        if errors not in ('strict', 'warn', 'ignore'):
            raise ValueError("invalid errors parameter")

        try:
            dirs = self.dirs()
        except Exception:
            if errors == 'ignore':
                return
            elif errors == 'warn':
                warnings.warn(
                    "Unable to list directory '%s': %s"
                    % (self, sys.exc_info()[1]),
                    TreeWalkWarning)
                return
            else:
                raise

        for child in dirs:
            if pattern is None or child.fnmatch(pattern):
                yield child
            for subsubdir in child.walkdirs(pattern, errors):
                yield subsubdir

    def walkfiles(self, pattern=None, errors='strict'):
        """ D.walkfiles() -> iterator over files in D, recursively.

        The optional argument, pattern, limits the results to files
        with names that match the pattern.  For example,
        ``mydir.walkfiles('*.tmp')`` yields only files with the .tmp
        extension.
        """
        if errors not in ('strict', 'warn', 'ignore'):
            raise ValueError("invalid errors parameter")

        try:
            childList = self.listdir()
        except Exception:
            if errors == 'ignore':
                return
            elif errors == 'warn':
                warnings.warn(
                    "Unable to list directory '%s': %s"
                    % (self, sys.exc_info()[1]),
                    TreeWalkWarning)
                return
            else:
                raise

        for child in childList:
            try:
                isfile = child.isfile()
                isdir = not isfile and child.isdir()
            except:
                if errors == 'ignore':
                    continue
                elif errors == 'warn':
                    warnings.warn(
                        "Unable to access '%s': %s"
                        % (self, sys.exc_info()[1]),
                        TreeWalkWarning)
                    continue
                else:
                    raise

            if isfile:
                if pattern is None or child.fnmatch(pattern):
                    yield child
            elif isdir:
                for f in child.walkfiles(pattern, errors):
                    yield f

    def fnmatch(self, pattern):
        """ Return True if self.name matches the given pattern.

        pattern - A filename pattern with wildcards,
            for example ``'*.py'``.
        """
        return fnmatch.fnmatch(self.name, pattern)

    def glob(self, pattern):
        """ Return a list of path objects that match the pattern.

        pattern - a path relative to this directory, with wildcards.

        For example, path('/users').glob('*/bin/*') returns a list
        of all the files users have in their bin directories.
        """
        cls = self._next_class
        return [cls(s) for s in glob.glob(self / pattern)]

    #
    # --- Reading or writing an entire file at once.

    def open(self, *args, **kwargs):
        """ Open this file.  Return a file object. """
        return open(self, *args, **kwargs)

    def bytes(self):
        """ Open this file, read all bytes, return them as a string. """
        with self.open('rb') as f:
            return f.read()

    def chunks(self, size, *args, **kwargs):
        """ Returns a generator yielding chunks of the file, so it can
            be read piece by piece with a simple for loop.

           Any argument you pass after `size` will be passed to `open()`.

           :example:

               >>> for chunk in path("file.txt").chunk(8192):
               ...    print(chunk)

            This will read the file by chunks of 8192 bytes.
        """
        with open(self, *args, **kwargs) as f:
            while True:
                d = f.read(size)
                if not d:
                    break
                yield d

    def write_bytes(self, bytes, append=False):
        """ Open this file and write the given bytes to it.

        Default behavior is to overwrite any existing file.
        Call p.write_bytes(bytes, append=True) to append instead.
        """
        if append:
            mode = 'ab'
        else:
            mode = 'wb'
        with self.open(mode) as f:
            f.write(bytes)

    def text(self, encoding=None, errors='strict'):
        r""" Open this file, read it in, return the content as a string.

        This method uses 'U' mode, so '\r\n' and '\r' are automatically
        translated to '\n'.

        Optional arguments:

        encoding - The Unicode encoding (or character set) of
            the file.  If present, the content of the file is
            decoded and returned as a unicode object; otherwise
            it is returned as an 8-bit str.
        errors - How to handle Unicode errors; see help(str.decode)
            for the options.  Default is 'strict'.
        """
        if encoding is None:
            # 8-bit
            with self.open('U') as f:
                return f.read()
        else:
            # Unicode
            with codecs.open(self, 'r', encoding, errors) as f:
                # (Note - Can't use 'U' mode here, since codecs.open
                # doesn't support 'U' mode.)
                t = f.read()
            return (t.replace(u('\r\n'), u('\n'))
                     .replace(u('\r\x85'), u('\n'))
                     .replace(u('\r'), u('\n'))
                     .replace(u('\x85'), u('\n'))
                     .replace(u('\u2028'), u('\n')))

    def write_text(self, text, encoding=None, errors='strict',
                   linesep=os.linesep, append=False):
        r""" Write the given text to this file.

        The default behavior is to overwrite any existing file;
        to append instead, use the 'append=True' keyword argument.

        There are two differences between path.write_text() and
        path.write_bytes(): newline handling and Unicode handling.
        See below.

        Parameters:

          - text - str/unicode - The text to be written.

          - encoding - str - The Unicode encoding that will be used.
            This is ignored if 'text' isn't a Unicode string.

          - errors - str - How to handle Unicode encoding errors.
            Default is 'strict'.  See help(unicode.encode) for the
            options.  This is ignored if 'text' isn't a Unicode
            string.

          - linesep - keyword argument - str/unicode - The sequence of
            characters to be used to mark end-of-line.  The default is
            os.linesep.  You can also specify None; this means to
            leave all newlines as they are in 'text'.

          - append - keyword argument - bool - Specifies what to do if
            the file already exists (True: append to the end of it;
            False: overwrite it.)  The default is False.


        --- Newline handling.

        write_text() converts all standard end-of-line sequences
        ('\n', '\r', and '\r\n') to your platform's default end-of-line
        sequence (see os.linesep; on Windows, for example, the
        end-of-line marker is '\r\n').

        If you don't like your platform's default, you can override it
        using the 'linesep=' keyword argument.  If you specifically want
        write_text() to preserve the newlines as-is, use 'linesep=None'.

        This applies to Unicode text the same as to 8-bit text, except
        there are three additional standard Unicode end-of-line sequences:
        u'\x85', u'\r\x85', and u'\u2028'.

        (This is slightly different from when you open a file for
        writing with fopen(filename, "w") in C or open(filename, 'w')
        in Python.)


        --- Unicode

        If 'text' isn't Unicode, then apart from newline handling, the
        bytes are written verbatim to the file.  The 'encoding' and
        'errors' arguments are not used and must be omitted.

        If 'text' is Unicode, it is first converted to bytes using the
        specified 'encoding' (or the default encoding if 'encoding'
        isn't specified).  The 'errors' argument applies only to this
        conversion.

        """
        if isinstance(text, unicode):
            if linesep is not None:
                # Convert all standard end-of-line sequences to
                # ordinary newline characters.
                text = (text.replace(u('\r\n'), u('\n'))
                            .replace(u('\r\x85'), u('\n'))
                            .replace(u('\r'), u('\n'))
                            .replace(u('\x85'), u('\n'))
                            .replace(u('\u2028'), u('\n')))
                text = text.replace(u('\n'), linesep)
            if encoding is None:
                encoding = sys.getdefaultencoding()
            bytes = text.encode(encoding, errors)
        else:
            # It is an error to specify an encoding if 'text' is
            # an 8-bit string.
            assert encoding is None

            if linesep is not None:
                text = (text.replace('\r\n', '\n')
                            .replace('\r', '\n'))
                bytes = text.replace('\n', linesep)

        self.write_bytes(bytes, append)

    def lines(self, encoding=None, errors='strict', retain=True):
        r""" Open this file, read all lines, return them in a list.

        Optional arguments:
            encoding - The Unicode encoding (or character set) of
                the file.  The default is None, meaning the content
                of the file is read as 8-bit characters and returned
                as a list of (non-Unicode) str objects.
            errors - How to handle Unicode errors; see help(str.decode)
                for the options.  Default is 'strict'
            retain - If true, retain newline characters; but all newline
                character combinations ('\r', '\n', '\r\n') are
                translated to '\n'.  If false, newline characters are
                stripped off.  Default is True.

        This uses 'U' mode.
        """
        if encoding is None and retain:
            with self.open('U') as f:
                return f.readlines()
        else:
            return self.text(encoding, errors).splitlines(retain)

    def write_lines(self, lines, encoding=None, errors='strict',
                    linesep=os.linesep, append=False):
        r""" Write the given lines of text to this file.

        By default this overwrites any existing file at this path.

        This puts a platform-specific newline sequence on every line.
        See 'linesep' below.

        lines - A list of strings.

        encoding - A Unicode encoding to use.  This applies only if
            'lines' contains any Unicode strings.

        errors - How to handle errors in Unicode encoding.  This
            also applies only to Unicode strings.

        linesep - The desired line-ending.  This line-ending is
            applied to every line.  If a line already has any
            standard line ending ('\r', '\n', '\r\n', u'\x85',
            u'\r\x85', u'\u2028'), that will be stripped off and
            this will be used instead.  The default is os.linesep,
            which is platform-dependent ('\r\n' on Windows, '\n' on
            Unix, etc.)  Specify None to write the lines as-is,
            like file.writelines().

        Use the keyword argument append=True to append lines to the
        file.  The default is to overwrite the file.  Warning:
        When you use this with Unicode data, if the encoding of the
        existing data in the file is different from the encoding
        you specify with the encoding= parameter, the result is
        mixed-encoding data, which can really confuse someone trying
        to read the file later.
        """
        if append:
            mode = 'ab'
        else:
            mode = 'wb'
        with self.open(mode) as f:
            for line in lines:
                isUnicode = isinstance(line, unicode)
                if linesep is not None:
                    # Strip off any existing line-end and add the
                    # specified linesep string.
                    if isUnicode:
                        if line[-2:] in (u('\r\n'), u('\x0d\x85')):
                            line = line[:-2]
                        elif line[-1:] in (u('\r'), u('\n'),
                                           u('\x85'), u('\u2028')):
                            line = line[:-1]
                    else:
                        if line[-2:] == '\r\n':
                            line = line[:-2]
                        elif line[-1:] in ('\r', '\n'):
                            line = line[:-1]
                    line += linesep
                if isUnicode:
                    if encoding is None:
                        encoding = sys.getdefaultencoding()
                    line = line.encode(encoding, errors)
                f.write(line)

    def read_md5(self):
        """ Calculate the md5 hash for this file.

        This reads through the entire file.
        """
        return self.read_hash('md5')

    def _hash(self, hash_name):
        """ Returns a hash object for the file at the current path.

            `hash_name` should be a hash algo name such as 'md5' or 'sha1'
            that's available in the `hashlib` module.
        """
        m = hashlib.new(hash_name)
        for chunk in self.chunks(8192):
            m.update(chunk)
        return m

    def read_hash(self, hash_name):
        """ Calculate given hash for this file.

        List of supported hashes can be obtained from hashlib package. This
        reads the entire file.
        """
        return self._hash(hash_name).digest()

    def read_hexhash(self, hash_name):
        """ Calculate given hash for this file, returning hexdigest.

        List of supported hashes can be obtained from hashlib package. This
        reads the entire file.
        """
        return self._hash(hash_name).hexdigest()

    # --- Methods for querying the filesystem.
    # N.B. On some platforms, the os.path functions may be implemented in C
    # (e.g. isdir on Windows, Python 3.2.2), and compiled functions don't get
    # bound. Playing it safe and wrapping them all in method calls.

    def isabs(self):
        return self.module.isabs(self)

    def exists(self):
        return self.module.exists(self)

    def isdir(self):
        return self.module.isdir(self)

    def isfile(self):
        return self.module.isfile(self)

    def islink(self):
        return self.module.islink(self)

    def ismount(self):
        return self.module.ismount(self)

    def samefile(self, other):
        return self.module.samefile(self, other)

    def getatime(self):
        return self.module.getatime(self)

    atime = property(
        getatime, None, None,
        """ Last access time of the file. """)

    def getmtime(self):
        return self.module.getmtime(self)

    mtime = property(
        getmtime, None, None,
        """ Last-modified time of the file. """)

    def getctime(self):
        return self.module.getctime(self)

    ctime = property(
        getctime, None, None,
        """ Creation time of the file. """)

    def getsize(self):
        return self.module.getsize(self)

    size = property(
        getsize, None, None,
        """ Size of the file, in bytes. """)

    if hasattr(os, 'access'):
        def access(self, mode):
            """ Return true if current user has access to this path.

            mode - One of the constants os.F_OK, os.R_OK, os.W_OK, os.X_OK
            """
            return os.access(self, mode)

    def stat(self):
        """ Perform a stat() system call on this path. """
        return os.stat(self)

    def lstat(self):
        """ Like path.stat(), but do not follow symbolic links. """
        return os.lstat(self)

    def __get_owner_windows(self):
        r"""
        Return the name of the owner of this file or directory. Follow
        symbolic links.

        Return a name of the form ur'DOMAIN\User Name'; may be a group.
        """
        desc = win32security.GetFileSecurity(
            self, win32security.OWNER_SECURITY_INFORMATION)
        sid = desc.GetSecurityDescriptorOwner()
        account, domain, typecode = win32security.LookupAccountSid(None, sid)
        return domain + u('\\') + account

    def __get_owner_unix(self):
        """
        Return the name of the owner of this file or directory. Follow
        symbolic links.
        """
        st = self.stat()
        return pwd.getpwuid(st.st_uid).pw_name

    def __get_owner_not_implemented(self):
        raise NotImplementedError("Ownership not available on this platform.")

    if 'win32security' in globals():
        get_owner = __get_owner_windows
    elif 'pwd' in globals():
        get_owner = __get_owner_unix
    else:
        get_owner = __get_owner_not_implemented

    owner = property(
        get_owner, None, None,
        """ Name of the owner of this file or directory. """)

    if hasattr(os, 'statvfs'):
        def statvfs(self):
            """ Perform a statvfs() system call on this path. """
            return os.statvfs(self)

    if hasattr(os, 'pathconf'):
        def pathconf(self, name):
            return os.pathconf(self, name)

    #
    # --- Modifying operations on files and directories

    def utime(self, times):
        """ Set the access and modified times of this file. """
        os.utime(self, times)
        return self

    def chmod(self, mode):
        os.chmod(self, mode)
        return self

    if hasattr(os, 'chown'):
        def chown(self, uid=-1, gid=-1):
            os.chown(self, uid, gid)
            return self

    def rename(self, new):
        os.rename(self, new)
        return self._next_class(new)

    def renames(self, new):
        os.renames(self, new)
        return self._next_class(new)

    #
    # --- Create/delete operations on directories

    def mkdir(self, mode=o777):
        os.mkdir(self, mode)
        return self

    def mkdir_p(self, mode=o777):
        try:
            self.mkdir(mode)
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.EEXIST:
                raise
        return self

    def makedirs(self, mode=o777):
        os.makedirs(self, mode)
        return self

    def makedirs_p(self, mode=o777):
        try:
            self.makedirs(mode)
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.EEXIST:
                raise
        return self

    def rmdir(self):
        os.rmdir(self)
        return self

    def rmdir_p(self):
        try:
            self.rmdir()
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.ENOTEMPTY and e.errno != errno.EEXIST:
                raise
        return self

    def removedirs(self):
        os.removedirs(self)
        return self

    def removedirs_p(self):
        try:
            self.removedirs()
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.ENOTEMPTY and e.errno != errno.EEXIST:
                raise
        return self

    # --- Modifying operations on files

    def touch(self):
        """ Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        fd = os.open(self, os.O_WRONLY | os.O_CREAT, o666)
        os.close(fd)
        os.utime(self, None)
        return self

    def remove(self):
        os.remove(self)
        return self

    def remove_p(self):
        try:
            self.unlink()
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.ENOENT:
                raise
        return self

    def unlink(self):
        os.unlink(self)
        return self

    def unlink_p(self):
        self.remove_p()
        return self

    # --- Links

    if hasattr(os, 'link'):
        def link(self, newpath):
            """ Create a hard link at 'newpath', pointing to this file. """
            os.link(self, newpath)
            return self._next_class(newpath)

    if hasattr(os, 'symlink'):
        def symlink(self, newlink):
            """ Create a symbolic link at 'newlink', pointing here. """
            os.symlink(self, newlink)
            return self._next_class(newlink)

    if hasattr(os, 'readlink'):
        def readlink(self):
            """ Return the path to which this symbolic link points.

            The result may be an absolute or a relative path.
            """
            return self._next_class(os.readlink(self))

        def readlinkabs(self):
            """ Return the path to which this symbolic link points.

            The result is always an absolute path.
            """
            p = self.readlink()
            if p.isabs():
                return p
            else:
                return (self.parent / p).abspath()

    #
    # --- High-level functions from shutil

    copyfile = shutil.copyfile
    copymode = shutil.copymode
    copystat = shutil.copystat
    copy = shutil.copy
    copy2 = shutil.copy2
    copytree = shutil.copytree
    if hasattr(shutil, 'move'):
        move = shutil.move
    rmtree = shutil.rmtree

    def rmtree_p(self):
        try:
            self.rmtree()
        except OSError:
            _, e, _ = sys.exc_info()
            if e.errno != errno.ENOENT:
                raise
        return self

    def chdir(self):
        os.chdir(self)

    cd = chdir

    #
    # --- Special stuff from os

    if hasattr(os, 'chroot'):
        def chroot(self):
            os.chroot(self)

    if hasattr(os, 'startfile'):
        def startfile(self):
            os.startfile(self)
            return self


class tempdir(path):
    """
    A temporary directory via tempfile.mkdtemp, and constructed with the
    same parameters that you can use as a context manager.

    Example:

        with tempdir() as d:
            # do stuff with the path object "d"

        # here the directory is deleted automatically
    """

    @ClassProperty
    @classmethod
    def _next_class(cls):
        return path

    def __new__(cls, *args, **kwargs):
        dirname = tempfile.mkdtemp(*args, **kwargs)
        return super(tempdir, cls).__new__(cls, dirname)

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_value:
            self.rmtree()


def _permission_mask(mode):
    """
    Convert a Unix chmod symbolic mode like 'ugo+rwx' to a function
    suitable for applying to a mask to affect that change.

    >>> mask = _permission_mask('ugo+rwx')
    >>> oct(mask(o554))
    'o777'

    >>> oct(_permission_mask('gw-x')(o777))
    'o766'
    """
    parsed = re.match('(?P<who>[ugo]+)(?P<op>[-+])(?P<what>[rwx]+)$', mode)
    if not parsed:
        raise ValueError("Unrecognized symbolic mode", mode)
    spec_map = dict(r=4, w=2, x=1)
    spec = reduce(operator.or_, [spec_map[perm]
                  for perm in parsed.group('what')])
    # now apply spec to each in who
    shift_map = dict(u=6, g=3, o=0)
    mask = reduce(operator.or_, [spec << shift_map[subj]
                  for subj in parsed.group('who')])

    op = parsed.group('op')
    # if op is -, invert the mask
    if op == '-':
        mask ^= o777

    op_map = {'+': operator.or_, '-': operator.and_}
    return functools.partial(op_map[op], mask)
