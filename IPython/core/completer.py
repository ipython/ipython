"""Word completion for IPython.

This module is a fork of the rlcompleter module in the Python standard
library.  The original enhancements made to rlcompleter have been sent
upstream and were accepted as of Python 2.3, but we need a lot more
functionality specific to IPython, so this module will continue to live as an
IPython-specific utility.

Original rlcompleter documentation:

This requires the latest extension to the readline module (the
completes keywords, built-ins and globals in __main__; when completing
NAME.NAME..., it evaluates (!) the expression up to the last dot and
completes its attributes.

It's very cool to do "import string" type "string.", hit the
completion key (twice), and see the list of names defined by the
string module!

Tip: to use the tab key as the completion key, call

    readline.parse_and_bind("tab: complete")

Notes:

- Exceptions raised by the completer function are *ignored* (and
generally cause the completion to fail).  This is a feature -- since
readline sets the tty device in raw (or cbreak) mode, printing a
traceback wouldn't work well without some complicated hoopla to save,
reset and restore the tty state.

- The evaluation of the NAME.NAME... form may cause arbitrary
application defined code to be executed if an object with a
__getattr__ hook is found.  Since it is the responsibility of the
application (or the user) to enable this feature, I consider this an
acceptable risk.  More complicated expressions (e.g. function calls or
indexing operations) are *not* evaluated.

- GNU readline is also used by the built-in functions input() and
raw_input(), and thus these also benefit/suffer from the completer
features.  Clearly an interactive application can benefit by
specifying its own completer function and using raw_input() for all
its input.

- When the original stdin is not a tty device, GNU readline is never
used, and this module (and the readline module) are silently inactive.
"""

#*****************************************************************************
#
# Since this file is essentially a minimally modified copy of the rlcompleter
# module which is part of the standard Python distribution, I assume that the
# proper procedure is to maintain its copyright as belonging to the Python
# Software Foundation (in addition to my own, for all new code).
#
#       Copyright (C) 2008 IPython Development Team
#       Copyright (C) 2001 Fernando Perez. <fperez@colorado.edu>
#       Copyright (C) 2001 Python Software Foundation, www.python.org
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
#*****************************************************************************

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import __main__
import glob
import inspect
import itertools
import keyword
import os
import re
import shlex
import sys

from IPython.config.configurable import Configurable
from IPython.core.error import TryNext
from IPython.core.inputsplitter import ESC_MAGIC
from IPython.utils import generics
from IPython.utils import io
from IPython.utils.dir2 import dir2
from IPython.utils.process import arg_split
from IPython.utils.traitlets import CBool, Enum

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# Public API
__all__ = ['Completer','IPCompleter']

if sys.platform == 'win32':
    PROTECTABLES = ' '
else:
    PROTECTABLES = ' ()[]{}?=\\|;:\'#*"^&'

#-----------------------------------------------------------------------------
# Main functions and classes
#-----------------------------------------------------------------------------

def has_open_quotes(s):
    """Return whether a string has open quotes.

    This simply counts whether the number of quote characters of either type in
    the string is odd.

    Returns
    -------
    If there is an open quote, the quote character is returned.  Else, return
    False.
    """
    # We check " first, then ', so complex cases with nested quotes will get
    # the " to take precedence.
    if s.count('"') % 2:
        return '"'
    elif s.count("'") % 2:
        return "'"
    else:
        return False


def protect_filename(s):
    """Escape a string to protect certain characters."""

    return "".join([(ch in PROTECTABLES and '\\' + ch or ch)
                    for ch in s])

def expand_user(path):
    """Expand '~'-style usernames in strings.

    This is similar to :func:`os.path.expanduser`, but it computes and returns
    extra information that will be useful if the input was being used in
    computing completions, and you wish to return the completions with the
    original '~' instead of its expanded value.

    Parameters
    ----------
    path : str
      String to be expanded.  If no ~ is present, the output is the same as the
      input.

    Returns
    -------
    newpath : str
      Result of ~ expansion in the input path.
    tilde_expand : bool
      Whether any expansion was performed or not.
    tilde_val : str
      The value that ~ was replaced with.
    """
    # Default values
    tilde_expand = False
    tilde_val = ''
    newpath = path

    if path.startswith('~'):
        tilde_expand = True
        rest = len(path)-1
        newpath = os.path.expanduser(path)
        if rest:
            tilde_val = newpath[:-rest]
        else:
            tilde_val = newpath

    return newpath, tilde_expand, tilde_val


def compress_user(path, tilde_expand, tilde_val):
    """Does the opposite of expand_user, with its outputs.
    """
    if tilde_expand:
        return path.replace(tilde_val, '~')
    else:
        return path


class Bunch(object): pass


DELIMS = ' \t\n`!@#$^&*()=+[{]}\\|;:\'",<>?'
GREEDY_DELIMS = ' \r\n'


class CompletionSplitter(object):
    """An object to split an input line in a manner similar to readline.

    By having our own implementation, we can expose readline-like completion in
    a uniform manner to all frontends.  This object only needs to be given the
    line of text to be split and the cursor position on said line, and it
    returns the 'word' to be completed on at the cursor after splitting the
    entire line.

    What characters are used as splitting delimiters can be controlled by
    setting the `delims` attribute (this is a property that internally
    automatically builds the necessary regular expression)"""

    # Private interface

    # A string of delimiter characters.  The default value makes sense for
    # IPython's most typical usage patterns.
    _delims = DELIMS

    # The expression (a normal string) to be compiled into a regular expression
    # for actual splitting.  We store it as an attribute mostly for ease of
    # debugging, since this type of code can be so tricky to debug.
    _delim_expr = None

    # The regular expression that does the actual splitting
    _delim_re = None

    def __init__(self, delims=None):
        delims = CompletionSplitter._delims if delims is None else delims
        self.delims = delims

    @property
    def delims(self):
        """Return the string of delimiter characters."""
        return self._delims

    @delims.setter
    def delims(self, delims):
        """Set the delimiters for line splitting."""
        expr = '[' + ''.join('\\'+ c for c in delims) + ']'
        self._delim_re = re.compile(expr)
        self._delims = delims
        self._delim_expr = expr

    def split_line(self, line, cursor_pos=None):
        """Split a line of text with a cursor at the given position.
        """
        l = line if cursor_pos is None else line[:cursor_pos]
        return self._delim_re.split(l)[-1]


class Completer(Configurable):

    greedy = CBool(False, config=True,
        help="""Activate greedy completion

        This will enable completion on elements of lists, results of function calls, etc.,
        but can be unsafe because the code is actually evaluated on TAB.
        """
    )
    

    def __init__(self, namespace=None, global_namespace=None, config=None, **kwargs):
        """Create a new completer for the command line.

        Completer(namespace=ns,global_namespace=ns2) -> completer instance.

        If unspecified, the default namespace where completions are performed
        is __main__ (technically, __main__.__dict__). Namespaces should be
        given as dictionaries.

        An optional second namespace can be given.  This allows the completer
        to handle cases where both the local and global scopes need to be
        distinguished.

        Completer instances should be used as the completion mechanism of
        readline via the set_completer() call:

        readline.set_completer(Completer(my_namespace).complete)
        """

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = 1
        else:
            self.use_main_ns = 0
            self.namespace = namespace

        # The global namespace, if given, can be bound directly
        if global_namespace is None:
            self.global_namespace = {}
        else:
            self.global_namespace = global_namespace

        super(Completer, self).__init__(config=config, **kwargs)

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if state == 0:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def global_matches(self, text):
        """Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions and names currently
        defined in self.namespace or self.global_namespace that match.

        """
        #print 'Completer->global_matches, txt=%r' % text # dbg
        matches = []
        match_append = matches.append
        n = len(text)
        for lst in [keyword.kwlist,
                    __builtin__.__dict__.keys(),
                    self.namespace.keys(),
                    self.global_namespace.keys()]:
            for word in lst:
                if word[:n] == text and word != "__builtins__":
                    match_append(word)
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace or self.global_namespace, it will be
        evaluated and its attributes (as revealed by dir()) are used as
        possible completions.  (For class instances, class members are are
        also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """

        #io.rprint('Completer->attr_matches, txt=%r' % text) # dbg
        # Another option, seems to work great. Catches things like ''.<tab>
        m = re.match(r"(\S+(\.\w+)*)\.(\w*)$", text)
    
        if m:
            expr, attr = m.group(1, 3)
        elif self.greedy:
            m2 = re.match(r"(.+)\.(\w*)$", self.line_buffer)
            if not m2:
                return []
            expr, attr = m2.group(1,2)
        else:
            return []
    
        try:
            obj = eval(expr, self.namespace)
        except:
            try:
                obj = eval(expr, self.global_namespace)
            except:
                return []

        if self.limit_to__all__ and hasattr(obj, '__all__'):
            words = get__all__entries(obj)
        else: 
            words = dir2(obj)

        try:
            words = generics.complete_object(obj, words)
        except TryNext:
            pass
        except Exception:
            # Silence errors from completion function
            #raise # dbg
            pass
        # Build match list to return
        n = len(attr)
        res = ["%s.%s" % (expr, w) for w in words if w[:n] == attr ]
        return res


def get__all__entries(obj):
    """returns the strings in the __all__ attribute"""
    try:
        words = getattr(obj, '__all__')
    except:
        return []
    
    return [w for w in words if isinstance(w, basestring)]


class IPCompleter(Completer):
    """Extension of the completer class with IPython-specific features"""

    def _greedy_changed(self, name, old, new):
        """update the splitter and readline delims when greedy is changed"""
        if new:
            self.splitter.delims = GREEDY_DELIMS
        else:
            self.splitter.delims = DELIMS

        if self.readline:
            self.readline.set_completer_delims(self.splitter.delims)
    
    merge_completions = CBool(True, config=True,
        help="""Whether to merge completion results into a single list
        
        If False, only the completion results from the first non-empty
        completer will be returned.
        """
    )
    omit__names = Enum((0,1,2), default_value=2, config=True,
        help="""Instruct the completer to omit private method names
        
        Specifically, when completing on ``object.<tab>``.
        
        When 2 [default]: all names that start with '_' will be excluded.
        
        When 1: all 'magic' names (``__foo__``) will be excluded.
        
        When 0: nothing will be excluded.
        """
    )
    limit_to__all__ = CBool(default_value=False, config=True,
        help="""Instruct the completer to use __all__ for the completion
        
        Specifically, when completing on ``object.<tab>``.
        
        When True: only those names in obj.__all__ will be included.
        
        When False [default]: the __all__ attribute is ignored 
        """
    )

    def __init__(self, shell=None, namespace=None, global_namespace=None,
                 alias_table=None, use_readline=True,
                 config=None, **kwargs):
        """IPCompleter() -> completer

        Return a completer object suitable for use by the readline library
        via readline.set_completer().

        Inputs:

        - shell: a pointer to the ipython shell itself.  This is needed
        because this completer knows about magic functions, and those can
        only be accessed via the ipython instance.

        - namespace: an optional dict where completions are performed.

        - global_namespace: secondary optional dict for completions, to
        handle cases (such as IPython embedded inside functions) where
        both Python scopes are visible.

        - If alias_table is supplied, it should be a dictionary of aliases
        to complete.

        use_readline : bool, optional
          If true, use the readline library.  This completer can still function
          without readline, though in that case callers must provide some extra
          information on each call about the current line."""

        self.magic_escape = ESC_MAGIC
        self.splitter = CompletionSplitter()

        # Readline configuration, only used by the rlcompleter method.
        if use_readline:
            # We store the right version of readline so that later code
            import IPython.utils.rlineimpl as readline
            self.readline = readline
        else:
            self.readline = None

        # _greedy_changed() depends on splitter and readline being defined:
        Completer.__init__(self, namespace=namespace, global_namespace=global_namespace,
                            config=config, **kwargs)

        # List where completion matches will be stored
        self.matches = []
        self.shell = shell
        if alias_table is None:
            alias_table = {}
        self.alias_table = alias_table
        # Regexp to split filenames with spaces in them
        self.space_name_re = re.compile(r'([^\\] )')
        # Hold a local ref. to glob.glob for speed
        self.glob = glob.glob

        # Determine if we are running on 'dumb' terminals, like (X)Emacs
        # buffers, to avoid completion problems.
        term = os.environ.get('TERM','xterm')
        self.dumb_terminal = term in ['dumb','emacs']

        # Special handling of backslashes needed in win32 platforms
        if sys.platform == "win32":
            self.clean_glob = self._clean_glob_win32
        else:
            self.clean_glob = self._clean_glob

        #regexp to parse docstring for function signature
        self.docstring_sig_re = re.compile(r'^[\w|\s.]+\(([^)]*)\).*')
        self.docstring_kwd_re = re.compile(r'[\s|\[]*(\w+)(?:\s*=\s*.*)')
        #use this if positional argument name is also needed
        #= re.compile(r'[\s|\[]*(\w+)(?:\s*=?\s*.*)')

        # All active matcher routines for completion
        self.matchers = [self.python_matches,
                         self.file_matches,
                         self.magic_matches,
                         self.alias_matches,
                         self.python_func_kw_matches,
                         ]

    def all_completions(self, text):
        """
        Wrapper around the complete method for the benefit of emacs
        and pydb.
        """
        return self.complete(text)[1]

    def _clean_glob(self,text):
        return self.glob("%s*" % text)

    def _clean_glob_win32(self,text):
        return [f.replace("\\","/")
                for f in self.glob("%s*" % text)]

    def file_matches(self, text):
        """Match filenames, expanding ~USER type strings.

        Most of the seemingly convoluted logic in this completer is an
        attempt to handle filenames with spaces in them.  And yet it's not
        quite perfect, because Python's readline doesn't expose all of the
        GNU readline details needed for this to be done correctly.

        For a filename with a space in it, the printed completions will be
        only the parts after what's already been typed (instead of the
        full completions, as is normally done).  I don't think with the
        current (as of Python 2.3) Python readline it's possible to do
        better."""

        #io.rprint('Completer->file_matches: <%r>' % text) # dbg

        # chars that require escaping with backslash - i.e. chars
        # that readline treats incorrectly as delimiters, but we
        # don't want to treat as delimiters in filename matching
        # when escaped with backslash
        if text.startswith('!'):
            text = text[1:]
            text_prefix = '!'
        else:
            text_prefix = ''

        text_until_cursor = self.text_until_cursor
        # track strings with open quotes
        open_quotes = has_open_quotes(text_until_cursor)

        if '(' in text_until_cursor or '[' in text_until_cursor:
            lsplit = text
        else:
            try:
                # arg_split ~ shlex.split, but with unicode bugs fixed by us
                lsplit = arg_split(text_until_cursor)[-1]
            except ValueError:
                # typically an unmatched ", or backslash without escaped char.
                if open_quotes:
                    lsplit = text_until_cursor.split(open_quotes)[-1]
                else:
                    return []
            except IndexError:
                # tab pressed on empty line
                lsplit = ""

        if not open_quotes and lsplit != protect_filename(lsplit):
            # if protectables are found, do matching on the whole escaped name
            has_protectables = True
            text0,text = text,lsplit
        else:
            has_protectables = False
            text = os.path.expanduser(text)

        if text == "":
            return [text_prefix + protect_filename(f) for f in self.glob("*")]

        # Compute the matches from the filesystem
        m0 = self.clean_glob(text.replace('\\',''))

        if has_protectables:
            # If we had protectables, we need to revert our changes to the
            # beginning of filename so that we don't double-write the part
            # of the filename we have so far
            len_lsplit = len(lsplit)
            matches = [text_prefix + text0 +
                       protect_filename(f[len_lsplit:]) for f in m0]
        else:
            if open_quotes:
                # if we have a string with an open quote, we don't need to
                # protect the names at all (and we _shouldn't_, as it
                # would cause bugs when the filesystem call is made).
                matches = m0
            else:
                matches = [text_prefix +
                           protect_filename(f) for f in m0]

        #io.rprint('mm', matches)  # dbg

        # Mark directories in input list by appending '/' to their names.
        matches = [x+'/' if os.path.isdir(x) else x for x in matches]
        return matches

    def magic_matches(self, text):
        """Match magics"""
        #print 'Completer->magic_matches:',text,'lb',self.text_until_cursor # dbg
        # Get all shell magics now rather than statically, so magics loaded at
        # runtime show up too.
        lsm = self.shell.magics_manager.lsmagic()
        line_magics = lsm['line']
        cell_magics = lsm['cell']
        pre = self.magic_escape
        pre2 = pre+pre
        
        # Completion logic:
        # - user gives %%: only do cell magics
        # - user gives %: do both line and cell magics
        # - no prefix: do both
        # In other words, line magics are skipped if the user gives %% explicitly
        bare_text = text.lstrip(pre)
        comp = [ pre2+m for m in cell_magics if m.startswith(bare_text)]
        if not text.startswith(pre2):
            comp += [ pre+m for m in line_magics if m.startswith(bare_text)]
        return comp

    def alias_matches(self, text):
        """Match internal system aliases"""
        #print 'Completer->alias_matches:',text,'lb',self.text_until_cursor # dbg

        # if we are not in the first 'item', alias matching
        # doesn't make sense - unless we are starting with 'sudo' command.
        main_text = self.text_until_cursor.lstrip()
        if ' ' in main_text and not main_text.startswith('sudo'):
            return []
        text = os.path.expanduser(text)
        aliases =  self.alias_table.keys()
        if text == '':
            return aliases
        else:
            return [a for a in aliases if a.startswith(text)]

    def python_matches(self,text):
        """Match attributes or global python names"""
        
        #io.rprint('Completer->python_matches, txt=%r' % text) # dbg
        if "." in text:
            try:
                matches = self.attr_matches(text)
                if text.endswith('.') and self.omit__names:
                    if self.omit__names == 1:
                        # true if txt is _not_ a __ name, false otherwise:
                        no__name = (lambda txt:
                                    re.match(r'.*\.__.*?__',txt) is None)
                    else:
                        # true if txt is _not_ a _ name, false otherwise:
                        no__name = (lambda txt:
                                    re.match(r'.*\._.*?',txt) is None)
                    matches = filter(no__name, matches)
            except NameError:
                # catches <undefined attributes>.<tab>
                matches = []
        else:
            matches = self.global_matches(text)

        return matches

    def _default_arguments_from_docstring(self, doc):
        """Parse the first line of docstring for call signature.

        Docstring should be of the form 'min(iterable[, key=func])\n'.
        It can also parse cython docstring of the form
        'Minuit.migrad(self, int ncall=10000, resume=True, int nsplit=1)'.
        """
        if doc is None:
            return []

        #care only the firstline
        line = doc.lstrip().splitlines()[0]

        #p = re.compile(r'^[\w|\s.]+\(([^)]*)\).*')
        #'min(iterable[, key=func])\n' -> 'iterable[, key=func]'
        sig = self.docstring_sig_re.search(line)
        if sig is None:
            return []
        # iterable[, key=func]' -> ['iterable[' ,' key=func]']
        sig = sig.groups()[0].split(',')
        ret = []
        for s in sig:
            #re.compile(r'[\s|\[]*(\w+)(?:\s*=\s*.*)')
            ret += self.docstring_kwd_re.findall(s)
        return ret

    def _default_arguments(self, obj):
        """Return the list of default arguments of obj if it is callable,
        or empty list otherwise."""
        call_obj = obj
        ret = []
        if inspect.isbuiltin(obj):
            pass
        elif not (inspect.isfunction(obj) or inspect.ismethod(obj)):
            if inspect.isclass(obj):
                #for cython embededsignature=True the constructor docstring
                #belongs to the object itself not __init__
                ret += self._default_arguments_from_docstring(
                            getattr(obj, '__doc__', ''))
                # for classes, check for __init__,__new__
                call_obj = (getattr(obj, '__init__', None) or
                       getattr(obj, '__new__', None))
            # for all others, check if they are __call__able
            elif hasattr(obj, '__call__'):
                call_obj = obj.__call__

        ret += self._default_arguments_from_docstring(
                 getattr(call_obj, '__doc__', ''))

        try:
            args,_,_1,defaults = inspect.getargspec(call_obj)
            if defaults:
                ret+=args[-len(defaults):]
        except TypeError:
            pass

        return list(set(ret))

    def python_func_kw_matches(self,text):
        """Match named parameters (kwargs) of the last open function"""
        
        if "." in text: # a parameter cannot be dotted
            return []
        try: regexp = self.__funcParamsRegex
        except AttributeError:
            regexp = self.__funcParamsRegex = re.compile(r'''
                '.*?(?<!\\)' |    # single quoted strings or
                ".*?(?<!\\)" |    # double quoted strings or
                \w+          |    # identifier
                \S                # other characters
                ''', re.VERBOSE | re.DOTALL)
        # 1. find the nearest identifier that comes before an unclosed
        # parenthesis before the cursor
        # e.g. for "foo (1+bar(x), pa<cursor>,a=1)", the candidate is "foo"
        tokens = regexp.findall(self.text_until_cursor)
        tokens.reverse()
        iterTokens = iter(tokens); openPar = 0

        for token in iterTokens:
            if token == ')':
                openPar -= 1
            elif token == '(':
                openPar += 1
                if openPar > 0:
                    # found the last unclosed parenthesis
                    break
        else:
            return []
        # 2. Concatenate dotted names ("foo.bar" for "foo.bar(x, pa" )
        ids = []
        isId = re.compile(r'\w+$').match

        while True:
            try:
                ids.append(next(iterTokens))
                if not isId(ids[-1]):
                    ids.pop(); break
                if not next(iterTokens) == '.':
                    break
            except StopIteration:
                break
        # lookup the candidate callable matches either using global_matches
        # or attr_matches for dotted names
        if len(ids) == 1:
            callableMatches = self.global_matches(ids[0])
        else:
            callableMatches = self.attr_matches('.'.join(ids[::-1]))
        argMatches = []
        for callableMatch in callableMatches:
            try:
                namedArgs = self._default_arguments(eval(callableMatch,
                                                        self.namespace))
            except:
                continue

            for namedArg in namedArgs:
                if namedArg.startswith(text):
                    argMatches.append("%s=" %namedArg)
        return argMatches

    def dispatch_custom_completer(self, text):
        #io.rprint("Custom! '%s' %s" % (text, self.custom_completers)) # dbg
        line = self.line_buffer
        if not line.strip():
            return None

        # Create a little structure to pass all the relevant information about
        # the current completion to any custom completer.
        event = Bunch()
        event.line = line
        event.symbol = text
        cmd = line.split(None,1)[0]
        event.command = cmd
        event.text_until_cursor = self.text_until_cursor

        #print "\ncustom:{%s]\n" % event # dbg

        # for foo etc, try also to find completer for %foo
        if not cmd.startswith(self.magic_escape):
            try_magic = self.custom_completers.s_matches(
                self.magic_escape + cmd)
        else:
            try_magic = []

        for c in itertools.chain(self.custom_completers.s_matches(cmd),
                 try_magic,
                 self.custom_completers.flat_matches(self.text_until_cursor)):
            #print "try",c # dbg
            try:
                res = c(event)
                if res:
                    # first, try case sensitive match
                    withcase = [r for r in res if r.startswith(text)]
                    if withcase:
                        return withcase
                    # if none, then case insensitive ones are ok too
                    text_low = text.lower()
                    return [r for r in res if r.lower().startswith(text_low)]
            except TryNext:
                pass

        return None

    def complete(self, text=None, line_buffer=None, cursor_pos=None):
        """Find completions for the given text and line context.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        Note that both the text and the line_buffer are optional, but at least
        one of them must be given.

        Parameters
        ----------
          text : string, optional
            Text to perform the completion on.  If not given, the line buffer
            is split using the instance's CompletionSplitter object.

          line_buffer : string, optional
            If not given, the completer attempts to obtain the current line
            buffer via readline.  This keyword allows clients which are
            requesting for text completions in non-readline contexts to inform
            the completer of the entire text.

          cursor_pos : int, optional
            Index of the cursor in the full line buffer.  Should be provided by
            remote frontends where kernel has no access to frontend state.

        Returns
        -------
        text : str
          Text that was actually used in the completion.

        matches : list
          A list of completion matches.
        """
        #io.rprint('\nCOMP1 %r %r %r' % (text, line_buffer, cursor_pos))  # dbg

        # if the cursor position isn't given, the only sane assumption we can
        # make is that it's at the end of the line (the common case)
        if cursor_pos is None:
            cursor_pos = len(line_buffer) if text is None else len(text)

        # if text is either None or an empty string, rely on the line buffer
        if not text:
            text = self.splitter.split_line(line_buffer, cursor_pos)

        # If no line buffer is given, assume the input text is all there was
        if line_buffer is None:
            line_buffer = text

        self.line_buffer = line_buffer
        self.text_until_cursor = self.line_buffer[:cursor_pos]
        #io.rprint('COMP2 %r %r %r' % (text, line_buffer, cursor_pos))  # dbg

        # Start with a clean slate of completions
        self.matches[:] = []
        custom_res = self.dispatch_custom_completer(text)
        if custom_res is not None:
            # did custom completers produce something?
            self.matches = custom_res
        else:
            # Extend the list of completions with the results of each
            # matcher, so we return results to the user from all
            # namespaces.
            if self.merge_completions:
                self.matches = []
                for matcher in self.matchers:
                    try:
                        self.matches.extend(matcher(text))
                    except:
                        # Show the ugly traceback if the matcher causes an
                        # exception, but do NOT crash the kernel!
                        sys.excepthook(*sys.exc_info())
            else:
                for matcher in self.matchers:
                    self.matches = matcher(text)
                    if self.matches:
                        break
        # FIXME: we should extend our api to return a dict with completions for
        # different types of objects.  The rlcomplete() method could then
        # simply collapse the dict into a list for readline, but we'd have
        # richer completion semantics in other evironments.
        self.matches = sorted(set(self.matches))
        #io.rprint('COMP TEXT, MATCHES: %r, %r' % (text, self.matches)) # dbg
        return text, self.matches

    def rlcomplete(self, text, state):
        """Return the state-th possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        Parameters
        ----------
          text : string
            Text to perform the completion on.

          state : int
            Counter used by readline.
        """
        if state==0:

            self.line_buffer = line_buffer = self.readline.get_line_buffer()
            cursor_pos = self.readline.get_endidx()

            #io.rprint("\nRLCOMPLETE: %r %r %r" %
            #          (text, line_buffer, cursor_pos) ) # dbg

            # if there is only a tab on a line with only whitespace, instead of
            # the mostly useless 'do you want to see all million completions'
            # message, just do the right thing and give the user his tab!
            # Incidentally, this enables pasting of tabbed text from an editor
            # (as long as autoindent is off).

            # It should be noted that at least pyreadline still shows file
            # completions - is there a way around it?

            # don't apply this on 'dumb' terminals, such as emacs buffers, so
            # we don't interfere with their own tab-completion mechanism.
            if not (self.dumb_terminal or line_buffer.strip()):
                self.readline.insert_text('\t')
                sys.stdout.flush()
                return None

            # Note: debugging exceptions that may occur in completion is very
            # tricky, because readline unconditionally silences them.  So if
            # during development you suspect a bug in the completion code, turn
            # this flag on temporarily by uncommenting the second form (don't
            # flip the value in the first line, as the '# dbg' marker can be
            # automatically detected and is used elsewhere).
            DEBUG = False
            #DEBUG = True # dbg
            if DEBUG:
                try:
                    self.complete(text, line_buffer, cursor_pos)
                except:
                    import traceback; traceback.print_exc()
            else:
                # The normal production version is here

                # This method computes the self.matches array
                self.complete(text, line_buffer, cursor_pos)

        try:
            return self.matches[state]
        except IndexError:
            return None
