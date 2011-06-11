# encoding: utf-8
"""
Utilities for working with strings and text.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __main__

import os
import re
import shutil
from string import Formatter

from IPython.external.path import path

from IPython.utils.io import nlprint
from IPython.utils.data import flatten

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


def unquote_ends(istr):
    """Remove a single pair of quotes from the endpoints of a string."""

    if not istr:
        return istr
    if (istr[0]=="'" and istr[-1]=="'") or \
       (istr[0]=='"' and istr[-1]=='"'):
        return istr[1:-1]
    else:
        return istr


class LSString(str):
    """String derivative with a special access attributes.

    These are normal strings, but with the special attributes:

        .l (or .list) : value as list (split on newlines).
        .n (or .nlstr): original value (the string itself).
        .s (or .spstr): value as whitespace-separated string.
        .p (or .paths): list of path objects

    Any values which require transformations are computed only once and
    cached.

    Such strings are very useful to efficiently interact with the shell, which
    typically only understands whitespace-separated options for commands."""

    def get_list(self):
        try:
            return self.__list
        except AttributeError:
            self.__list = self.split('\n')
            return self.__list

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = self.replace('\n',' ')
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        return self

    n = nlstr = property(get_nlstr)

    def get_paths(self):
        try:
            return self.__paths
        except AttributeError:
            self.__paths = [path(p) for p in self.split('\n') if os.path.exists(p)]
            return self.__paths

    p = paths = property(get_paths)

# FIXME: We need to reimplement type specific displayhook and then add this
# back as a custom printer. This should also be moved outside utils into the
# core.

# def print_lsstring(arg):
#     """ Prettier (non-repr-like) and more informative printer for LSString """
#     print "LSString (.p, .n, .l, .s available). Value:"
#     print arg
# 
# 
# print_lsstring = result_display.when_type(LSString)(print_lsstring)


class SList(list):
    """List derivative with a special access attributes.

    These are normal lists, but with the special attributes:

        .l (or .list) : value as list (the list itself).
        .n (or .nlstr): value as a string, joined on newlines.
        .s (or .spstr): value as a string, joined on spaces.
        .p (or .paths): list of path objects

    Any values which require transformations are computed only once and
    cached."""

    def get_list(self):
        return self

    l = list = property(get_list)

    def get_spstr(self):
        try:
            return self.__spstr
        except AttributeError:
            self.__spstr = ' '.join(self)
            return self.__spstr

    s = spstr = property(get_spstr)

    def get_nlstr(self):
        try:
            return self.__nlstr
        except AttributeError:
            self.__nlstr = '\n'.join(self)
            return self.__nlstr

    n = nlstr = property(get_nlstr)

    def get_paths(self):
        try:
            return self.__paths
        except AttributeError:
            self.__paths = [path(p) for p in self if os.path.exists(p)]
            return self.__paths

    p = paths = property(get_paths)

    def grep(self, pattern, prune = False, field = None):
        """ Return all strings matching 'pattern' (a regex or callable)

        This is case-insensitive. If prune is true, return all items
        NOT matching the pattern.

        If field is specified, the match must occur in the specified
        whitespace-separated field.

        Examples::

            a.grep( lambda x: x.startswith('C') )
            a.grep('Cha.*log', prune=1)
            a.grep('chm', field=-1)
        """

        def match_target(s):
            if field is None:
                return s
            parts = s.split()
            try:
                tgt = parts[field]
                return tgt
            except IndexError:
                return ""

        if isinstance(pattern, basestring):
            pred = lambda x : re.search(pattern, x, re.IGNORECASE)
        else:
            pred = pattern
        if not prune:
            return SList([el for el in self if pred(match_target(el))])
        else:
            return SList([el for el in self if not pred(match_target(el))])

    def fields(self, *fields):
        """ Collect whitespace-separated fields from string list

        Allows quick awk-like usage of string lists.

        Example data (in var a, created by 'a = !ls -l')::
            -rwxrwxrwx  1 ville None      18 Dec 14  2006 ChangeLog
            drwxrwxrwx+ 6 ville None       0 Oct 24 18:05 IPython

        a.fields(0) is ['-rwxrwxrwx', 'drwxrwxrwx+']
        a.fields(1,0) is ['1 -rwxrwxrwx', '6 drwxrwxrwx+']
        (note the joining by space).
        a.fields(-1) is ['ChangeLog', 'IPython']

        IndexErrors are ignored.

        Without args, fields() just split()'s the strings.
        """
        if len(fields) == 0:
            return [el.split() for el in self]

        res = SList()
        for el in [f.split() for f in self]:
            lineparts = []

            for fd in fields:
                try:
                    lineparts.append(el[fd])
                except IndexError:
                    pass
            if lineparts:
                res.append(" ".join(lineparts))

        return res

    def sort(self,field= None,  nums = False):
        """ sort by specified fields (see fields())

        Example::
            a.sort(1, nums = True)

        Sorts a by second field, in numerical order (so that 21 > 3)

        """

        #decorate, sort, undecorate
        if field is not None:
            dsu = [[SList([line]).fields(field),  line] for line in self]
        else:
            dsu = [[line,  line] for line in self]
        if nums:
            for i in range(len(dsu)):
                numstr = "".join([ch for ch in dsu[i][0] if ch.isdigit()])
                try:
                    n = int(numstr)
                except ValueError:
                    n = 0;
                dsu[i][0] = n


        dsu.sort()
        return SList([t[1] for t in dsu])


# FIXME: We need to reimplement type specific displayhook and then add this
# back as a custom printer. This should also be moved outside utils into the
# core.

# def print_slist(arg):
#     """ Prettier (non-repr-like) and more informative printer for SList """
#     print "SList (.p, .n, .l, .s, .grep(), .fields(), sort() available):"
#     if hasattr(arg,  'hideonce') and arg.hideonce:
#         arg.hideonce = False
#         return
# 
#     nlprint(arg)
# 
# print_slist = result_display.when_type(SList)(print_slist)


def esc_quotes(strng):
    """Return the input string with single and double quotes escaped out"""

    return strng.replace('"','\\"').replace("'","\\'")


def make_quoted_expr(s):
    """Return string s in appropriate quotes, using raw string if possible.

    XXX - example removed because it caused encoding errors in documentation
    generation.  We need a new example that doesn't contain invalid chars.

    Note the use of raw string and padding at the end to allow trailing
    backslash.
    """

    tail = ''
    tailpadding = ''
    raw  = ''
    ucode = 'u'
    if "\\" in s:
        raw = 'r'
        if s.endswith('\\'):
            tail = '[:-1]'
            tailpadding = '_'
    if '"' not in s:
        quote = '"'
    elif "'" not in s:
        quote = "'"
    elif '"""' not in s and not s.endswith('"'):
        quote = '"""'
    elif "'''" not in s and not s.endswith("'"):
        quote = "'''"
    else:
        # give up, backslash-escaped string will do
        return '"%s"' % esc_quotes(s)
    res = ucode + raw + quote + s + tailpadding + quote + tail
    return res


def qw(words,flat=0,sep=None,maxsplit=-1):
    """Similar to Perl's qw() operator, but with some more options.

    qw(words,flat=0,sep=' ',maxsplit=-1) -> words.split(sep,maxsplit)

    words can also be a list itself, and with flat=1, the output will be
    recursively flattened.

    Examples:

    >>> qw('1 2')
    ['1', '2']

    >>> qw(['a b','1 2',['m n','p q']])
    [['a', 'b'], ['1', '2'], [['m', 'n'], ['p', 'q']]]

    >>> qw(['a b','1 2',['m n','p q']],flat=1)
    ['a', 'b', '1', '2', 'm', 'n', 'p', 'q']
    """

    if isinstance(words, basestring):
        return [word.strip() for word in words.split(sep,maxsplit)
                if word and not word.isspace() ]
    if flat:
        return flatten(map(qw,words,[1]*len(words)))
    return map(qw,words)


def qwflat(words,sep=None,maxsplit=-1):
    """Calls qw(words) in flat mode. It's just a convenient shorthand."""
    return qw(words,1,sep,maxsplit)


def qw_lol(indata):
    """qw_lol('a b') -> [['a','b']],
    otherwise it's just a call to qw().

    We need this to make sure the modules_some keys *always* end up as a
    list of lists."""

    if isinstance(indata, basestring):
        return [qw(indata)]
    else:
        return qw(indata)


def grep(pat,list,case=1):
    """Simple minded grep-like function.
    grep(pat,list) returns occurrences of pat in list, None on failure.

    It only does simple string matching, with no support for regexps. Use the
    option case=0 for case-insensitive matching."""

    # This is pretty crude. At least it should implement copying only references
    # to the original data in case it's big. Now it copies the data for output.
    out=[]
    if case:
        for term in list:
            if term.find(pat)>-1: out.append(term)
    else:
        lpat=pat.lower()
        for term in list:
            if term.lower().find(lpat)>-1: out.append(term)

    if len(out): return out
    else: return None


def dgrep(pat,*opts):
    """Return grep() on dir()+dir(__builtins__).

    A very common use of grep() when working interactively."""

    return grep(pat,dir(__main__)+dir(__main__.__builtins__),*opts)


def idgrep(pat):
    """Case-insensitive dgrep()"""

    return dgrep(pat,0)


def igrep(pat,list):
    """Synonym for case-insensitive grep."""

    return grep(pat,list,case=0)


def indent(instr,nspaces=4, ntabs=0, flatten=False):
    """Indent a string a given number of spaces or tabstops.

    indent(str,nspaces=4,ntabs=0) -> indent str by ntabs+nspaces.
    
    Parameters
    ----------
    
    instr : basestring
        The string to be indented.
    nspaces : int (default: 4)
        The number of spaces to be indented.
    ntabs : int (default: 0)
        The number of tabs to be indented.
    flatten : bool (default: False)
        Whether to scrub existing indentation.  If True, all lines will be
        aligned to the same indentation.  If False, existing indentation will
        be strictly increased.
    
    Returns
    -------
    
    str|unicode : string indented by ntabs and nspaces.
    
    """
    if instr is None:
        return
    ind = '\t'*ntabs+' '*nspaces
    if flatten:
        pat = re.compile(r'^\s*', re.MULTILINE)
    else:
        pat = re.compile(r'^', re.MULTILINE)
    outstr = re.sub(pat, ind, instr)
    if outstr.endswith(os.linesep+ind):
        return outstr[:-len(ind)]
    else:
        return outstr

def native_line_ends(filename,backup=1):
    """Convert (in-place) a file to line-ends native to the current OS.

    If the optional backup argument is given as false, no backup of the
    original file is left.  """

    backup_suffixes = {'posix':'~','dos':'.bak','nt':'.bak','mac':'.bak'}

    bak_filename = filename + backup_suffixes[os.name]

    original = open(filename).read()
    shutil.copy2(filename,bak_filename)
    try:
        new = open(filename,'wb')
        new.write(os.linesep.join(original.splitlines()))
        new.write(os.linesep) # ALWAYS put an eol at the end of the file
        new.close()
    except:
        os.rename(bak_filename,filename)
    if not backup:
        try:
            os.remove(bak_filename)
        except:
            pass


def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input.

    :Examples:

        In [7]: list_strings('A single string')
        Out[7]: ['A single string']

        In [8]: list_strings(['A single string in a list'])
        Out[8]: ['A single string in a list']

        In [9]: list_strings(['A','list','of','strings'])
        Out[9]: ['A', 'list', 'of', 'strings']
    """

    if isinstance(arg,basestring): return [arg]
    else: return arg


def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'.

    :Examples:

        In [16]: marquee('A test',40)
        Out[16]: '**************** A test ****************'

        In [17]: marquee('A test',40,'-')
        Out[17]: '---------------- A test ----------------'

        In [18]: marquee('A test',40,' ')
        Out[18]: '                 A test                 '

    """
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)/len(mark)/2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)


ini_spaces_re = re.compile(r'^(\s+)')

def num_ini_spaces(strng):
    """Return the number of initial spaces in a string"""

    ini_spaces = ini_spaces_re.match(strng)
    if ini_spaces:
        return ini_spaces.end()
    else:
        return 0


def format_screen(strng):
    """Format a string for screen printing.

    This removes some latex-type format codes."""
    # Paragraph continue
    par_re = re.compile(r'\\$',re.MULTILINE)
    strng = par_re.sub('',strng)
    return strng


class EvalFormatter(Formatter):
    """A String Formatter that allows evaluation of simple expressions.
    
    Any time a format key is not found in the kwargs,
    it will be tried as an expression in the kwargs namespace.
    
    This is to be used in templating cases, such as the parallel batch
    script templates, where simple arithmetic on arguments is useful.
    
    Examples
    --------
    
    In [1]: f = EvalFormatter()
    In [2]: f.format('{n/4}', n=8)
    Out[2]: '2'
    
    In [3]: f.format('{range(3)}')
    Out[3]: '[0, 1, 2]'

    In [4]: f.format('{3*2}')
    Out[4]: '6'
    """
    
    def get_value(self, key, args, kwargs):
        if isinstance(key, (int, long)):
            return args[key]
        elif key in kwargs:
            return kwargs[key]
        else:
            # evaluate the expression using kwargs as namespace
            try:
                return eval(key, kwargs)
            except Exception:
                # classify all bad expressions as key errors
                raise KeyError(key)


