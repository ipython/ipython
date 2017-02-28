# encoding: utf-8
"""Word completion for IPython.

This module started as fork of the rlcompleter module in the Python standard
library.  The original enhancements made to rlcompleter have been sent
upstream and were accepted as of Python 2.3,

"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Some of this code originated from rlcompleter in the Python standard library
# Copyright (C) 2001 Python Software Foundation, www.python.org

from __future__ import print_function

import __main__
import glob
import inspect
import itertools
import keyword
import os
import re
import sys
import unicodedata
import string
import warnings

from traitlets.config.configurable import Configurable
from IPython.core.error import TryNext
from IPython.core.inputsplitter import ESC_MAGIC
from IPython.core.latex_symbols import latex_symbols, reverse_latex_symbol
from IPython.utils import generics
from IPython.utils.decorators import undoc
from IPython.utils.dir2 import dir2, get_real_method
from IPython.utils.process import arg_split
from IPython.utils.py3compat import builtin_mod, string_types, PY3, cast_unicode_py2
from traitlets import Bool, Enum, observe


# Public API
__all__ = ['Completer','IPCompleter']

if sys.platform == 'win32':
    PROTECTABLES = ' '
else:
    PROTECTABLES = ' ()[]{}?=\\|;:\'#*"^&'


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
    if set(s) & set(PROTECTABLES):
        if sys.platform == "win32":
            return '"' + s + '"'
        else:
            return "".join(("\\" + c if c in PROTECTABLES else c) for c in s)
    else:
        return s


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


def completions_sorting_key(word):
    """key for sorting completions

    This does several things:

    - Lowercase all completions, so they are sorted alphabetically with
      upper and lower case words mingled
    - Demote any completions starting with underscores to the end
    - Insert any %magic and %%cellmagic completions in the alphabetical order
      by their name
    """
    # Case insensitive sort
    word = word.lower()

    prio1, prio2 = 0, 0

    if word.startswith('__'):
        prio1 = 2
    elif word.startswith('_'):
        prio1 = 1

    if word.endswith('='):
        prio1 = -1

    if word.startswith('%%'):
        # If there's another % in there, this is something else, so leave it alone
        if not "%" in word[2:]:
            word = word[2:]
            prio2 = 2
    elif word.startswith('%'):
        if not "%" in word[1:]:
            word = word[1:]
            prio2 = 1

    return prio1, word, prio2


@undoc
class Bunch(object): pass


if sys.platform == 'win32':
    DELIMS = ' \t\n`!@#$^&*()=+[{]}|;\'",<>?'
else:
    DELIMS = ' \t\n`!@#$^&*()=+[{]}\\|;:\'",<>?'

GREEDY_DELIMS = ' =\r\n'


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

    greedy = Bool(False,
        help="""Activate greedy completion
        PENDING DEPRECTION. this is now mostly taken care of with Jedi.

        This will enable completion on elements of lists, results of function calls, etc.,
        but can be unsafe because the code is actually evaluated on TAB.
        """
    ).tag(config=True)

    backslash_combining_completions = Bool(True, 
        help="Enable unicode completions, e.g. \\alpha<tab> . "
             "Includes completion of latex commands, unicode names, and expanding "
             "unicode characters back to latex commands.").tag(config=True)

    def __init__(self, namespace=None, global_namespace=None, **kwargs):
        """Create a new completer for the command line.

        Completer(namespace=ns, global_namespace=ns2) -> completer instance.

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

        super(Completer, self).__init__(**kwargs)

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
        matches = []
        match_append = matches.append
        n = len(text)
        for lst in [keyword.kwlist,
                    builtin_mod.__dict__.keys(),
                    self.namespace.keys(),
                    self.global_namespace.keys()]:
            for word in lst:
                if word[:n] == text and word != "__builtins__":
                    match_append(word)
        return [cast_unicode_py2(m) for m in matches]

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
        return [u"%s.%s" % (expr, w) for w in words if w[:n] == attr ]


def get__all__entries(obj):
    """returns the strings in the __all__ attribute"""
    try:
        words = getattr(obj, '__all__')
    except:
        return []
    
    return [cast_unicode_py2(w) for w in words if isinstance(w, string_types)]


def match_dict_keys(keys, prefix, delims):
    """Used by dict_key_matches, matching the prefix to a list of keys"""
    if not prefix:
        return None, 0, [repr(k) for k in keys
                      if isinstance(k, (string_types, bytes))]
    quote_match = re.search('["\']', prefix)
    quote = quote_match.group()
    try:
        prefix_str = eval(prefix + quote, {})
    except Exception:
        return None, 0, []

    pattern = '[^' + ''.join('\\' + c for c in delims) + ']*$'
    token_match = re.search(pattern, prefix, re.UNICODE)
    token_start = token_match.start()
    token_prefix = token_match.group()

    # TODO: support bytes in Py3k
    matched = []
    for key in keys:
        try:
            if not key.startswith(prefix_str):
                continue
        except (AttributeError, TypeError, UnicodeError):
            # Python 3+ TypeError on b'a'.startswith('a') or vice-versa
            continue

        # reformat remainder of key to begin with prefix
        rem = key[len(prefix_str):]
        # force repr wrapped in '
        rem_repr = repr(rem + '"')
        if rem_repr.startswith('u') and prefix[0] not in 'uU':
            # Found key is unicode, but prefix is Py2 string.
            # Therefore attempt to interpret key as string.
            try:
                rem_repr = repr(rem.encode('ascii') + '"')
            except UnicodeEncodeError:
                continue

        rem_repr = rem_repr[1 + rem_repr.index("'"):-2]
        if quote == '"':
            # The entered prefix is quoted with ",
            # but the match is quoted with '.
            # A contained " hence needs escaping for comparison:
            rem_repr = rem_repr.replace('"', '\\"')

        # then reinsert prefix from start of token
        matched.append('%s%s' % (token_prefix, rem_repr))
    return quote, token_start, matched


def _safe_isinstance(obj, module, class_name):
    """Checks if obj is an instance of module.class_name if loaded
    """
    return (module in sys.modules and
            isinstance(obj, getattr(__import__(module), class_name)))


def back_unicode_name_matches(text):
    u"""Match unicode characters back to unicode name
    
    This does  ☃ -> \\snowman

    Note that snowman is not a valid python3 combining character but will be expanded.
    Though it will not recombine back to the snowman character by the completion machinery.

    This will not either back-complete standard sequences like \\n, \\b ...
    
    Used on Python 3 only.
    """
    if len(text)<2:
        return u'', ()
    maybe_slash = text[-2]
    if maybe_slash != '\\':
        return u'', ()

    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ['"',"'"]:
        return u'', ()
    try :
        unic = unicodedata.name(char)
        return '\\'+char,['\\'+unic]
    except KeyError:
        pass
    return u'', ()

def back_latex_name_matches(text):
    u"""Match latex characters back to unicode name
    
    This does  ->\\sqrt

    Used on Python 3 only.
    """
    if len(text)<2:
        return u'', ()
    maybe_slash = text[-2]
    if maybe_slash != '\\':
        return u'', ()


    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ['"',"'"]:
        return u'', ()
    try :
        latex = reverse_latex_symbol[char]
        # '\\' replace the \ as well
        return '\\'+char,[latex]
    except KeyError:
        pass
    return u'', ()


class IPCompleter(Completer):
    """Extension of the completer class with IPython-specific features"""
    
    @observe('greedy')
    def _greedy_changed(self, change):
        """update the splitter and readline delims when greedy is changed"""
        if change['new']:
            self.splitter.delims = GREEDY_DELIMS
        else:
            self.splitter.delims = DELIMS

        if self.readline:
            self.readline.set_completer_delims(self.splitter.delims)
    
    merge_completions = Bool(True,
        help="""Whether to merge completion results into a single list
        
        If False, only the completion results from the first non-empty
        completer will be returned.
        """
    ).tag(config=True)
    omit__names = Enum((0,1,2), default_value=2,
        help="""Instruct the completer to omit private method names
        
        Specifically, when completing on ``object.<tab>``.
        
        When 2 [default]: all names that start with '_' will be excluded.
        
        When 1: all 'magic' names (``__foo__``) will be excluded.
        
        When 0: nothing will be excluded.
        """
    ).tag(config=True)
    limit_to__all__ = Bool(False,
        help="""
        DEPRECATED as of version 5.0.
        
        Instruct the completer to use __all__ for the completion
        
        Specifically, when completing on ``object.<tab>``.
        
        When True: only those names in obj.__all__ will be included.
        
        When False [default]: the __all__ attribute is ignored 
        """,
    ).tag(config=True)

    @observe('limit_to__all__')
    def _limit_to_all_changed(self, change):
        warnings.warn('`IPython.core.IPCompleter.limit_to__all__` configuration '
            'value has been deprecated since IPython 5.0, will be made to have '
            'no effects and then removed in future version of IPython.',
            UserWarning)

    def __init__(self, shell=None, namespace=None, global_namespace=None,
                 use_readline=True, config=None, **kwargs):
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
        self.matchers = [
                         self.python_matches,
                         self.file_matches,
                         self.magic_matches,
                         self.python_func_kw_matches,
                         self.dict_key_matches,
                         ]

        # This is set externally by InteractiveShell
        self.custom_completers = None

    def all_completions(self, text):
        """
        Wrapper around the complete method for the benefit of emacs.
        """
        return self.complete(text)[1]

    def _clean_glob(self, text):
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

        # chars that require escaping with backslash - i.e. chars
        # that readline treats incorrectly as delimiters, but we
        # don't want to treat as delimiters in filename matching
        # when escaped with backslash
        if text.startswith('!'):
            text = text[1:]
            text_prefix = u'!'
        else:
            text_prefix = u''

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
            return [text_prefix + cast_unicode_py2(protect_filename(f)) for f in self.glob("*")]

        # Compute the matches from the filesystem
        if sys.platform == 'win32':
            m0 = self.clean_glob(text)
        else:
            m0 = self.clean_glob(text.replace('\\', ''))

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

        # Mark directories in input list by appending '/' to their names.
        return [cast_unicode_py2(x+'/') if os.path.isdir(x) else x for x in matches]

    def magic_matches(self, text):
        """Match magics"""
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
        return [cast_unicode_py2(c) for c in comp]


    def python_matches(self, text):
        """Match attributes or global python names"""
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
                                    re.match(r'\._.*?',txt[txt.rindex('.'):]) is None)
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

        if PY3:
            _keeps = (inspect.Parameter.KEYWORD_ONLY,
                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
            signature = inspect.signature
        else:
            import IPython.utils.signatures
            _keeps = (IPython.utils.signatures.Parameter.KEYWORD_ONLY,
                      IPython.utils.signatures.Parameter.POSITIONAL_OR_KEYWORD)
            signature = IPython.utils.signatures.signature

        try:
            sig = signature(call_obj)
            ret.extend(k for k, v in sig.parameters.items() if
                       v.kind in _keeps)
        except ValueError:
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
                    argMatches.append(u"%s=" %namedArg)
        return argMatches

    def dict_key_matches(self, text):
        "Match string keys in a dictionary, after e.g. 'foo[' "
        def get_keys(obj):
            # Objects can define their own completions by defining an
            # _ipy_key_completions_() method.
            method = get_real_method(obj, '_ipython_key_completions_')
            if method is not None:
                return method()

            # Special case some common in-memory dict-like types
            if isinstance(obj, dict) or\
               _safe_isinstance(obj, 'pandas', 'DataFrame'):
                try:
                    return list(obj.keys())
                except Exception:
                    return []
            elif _safe_isinstance(obj, 'numpy', 'ndarray') or\
                 _safe_isinstance(obj, 'numpy', 'void'):
                return obj.dtype.names or []
            return []

        try:
            regexps = self.__dict_key_regexps
        except AttributeError:
            dict_key_re_fmt = r'''(?x)
            (  # match dict-referring expression wrt greedy setting
                %s
            )
            \[   # open bracket
            \s*  # and optional whitespace
            ([uUbB]?  # string prefix (r not handled)
                (?:   # unclosed string
                    '(?:[^']|(?<!\\)\\')*
                |
                    "(?:[^"]|(?<!\\)\\")*
                )
            )?
            $
            '''
            regexps = self.__dict_key_regexps = {
                False: re.compile(dict_key_re_fmt % '''
                                  # identifiers separated by .
                                  (?!\d)\w+
                                  (?:\.(?!\d)\w+)*
                                  '''),
                True: re.compile(dict_key_re_fmt % '''
                                 .+
                                 ''')
            }

        match = regexps[self.greedy].search(self.text_until_cursor)
        if match is None:
            return []

        expr, prefix = match.groups()
        try:
            obj = eval(expr, self.namespace)
        except Exception:
            try:
                obj = eval(expr, self.global_namespace)
            except Exception:
                return []

        keys = get_keys(obj)
        if not keys:
            return keys
        closing_quote, token_offset, matches = match_dict_keys(keys, prefix, self.splitter.delims)
        if not matches:
            return matches
        
        # get the cursor position of
        # - the text being completed
        # - the start of the key text
        # - the start of the completion
        text_start = len(self.text_until_cursor) - len(text)
        if prefix:
            key_start = match.start(2)
            completion_start = key_start + token_offset
        else:
            key_start = completion_start = match.end()
        
        # grab the leading prefix, to make sure all completions start with `text`
        if text_start > key_start:
            leading = ''
        else:
            leading = text[text_start:completion_start]
        
        # the index of the `[` character
        bracket_idx = match.end(1)

        # append closing quote and bracket as appropriate
        # this is *not* appropriate if the opening quote or bracket is outside
        # the text given to this method
        suf = ''
        continuation = self.line_buffer[len(self.text_until_cursor):]
        if key_start > text_start and closing_quote:
            # quotes were opened inside text, maybe close them
            if continuation.startswith(closing_quote):
                continuation = continuation[len(closing_quote):]
            else:
                suf += closing_quote
        if bracket_idx > text_start:
            # brackets were opened inside text, maybe close them
            if not continuation.startswith(']'):
                suf += ']'
        
        return [leading + k + suf for k in matches]

    def unicode_name_matches(self, text):
        u"""Match Latex-like syntax for unicode characters base 
        on the name of the character.
        
        This does  \\GREEK SMALL LETTER ETA -> η

        Works only on valid python 3 identifier, or on combining characters that 
        will combine to form a valid identifier.
        
        Used on Python 3 only.
        """
        slashpos = text.rfind('\\')
        if slashpos > -1:
            s = text[slashpos+1:]
            try :
                unic = unicodedata.lookup(s)
                # allow combining chars
                if ('a'+unic).isidentifier():
                    return '\\'+s,[unic]
            except KeyError:
                pass
        return u'', []




    def latex_matches(self, text):
        u"""Match Latex syntax for unicode characters.
        
        This does both \\alp -> \\alpha and \\alpha -> α
        
        Used on Python 3 only.
        """
        slashpos = text.rfind('\\')
        if slashpos > -1:
            s = text[slashpos:]
            if s in latex_symbols:
                # Try to complete a full latex symbol to unicode
                # \\alpha -> α
                return s, [latex_symbols[s]]
            else:
                # If a user has partially typed a latex symbol, give them
                # a full list of options \al -> [\aleph, \alpha]
                matches = [k for k in latex_symbols if k.startswith(s)]
                return s, matches
        return u'', []

    def dispatch_custom_completer(self, text):
        if not self.custom_completers:
            return

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

        # for foo etc, try also to find completer for %foo
        if not cmd.startswith(self.magic_escape):
            try_magic = self.custom_completers.s_matches(
                self.magic_escape + cmd)
        else:
            try_magic = []

        for c in itertools.chain(self.custom_completers.s_matches(cmd),
                 try_magic,
                 self.custom_completers.flat_matches(self.text_until_cursor)):
            try:
                res = c(event)
                if res:
                    # first, try case sensitive match
                    withcase = [cast_unicode_py2(r) for r in res if r.startswith(text)]
                    if withcase:
                        return withcase
                    # if none, then case insensitive ones are ok too
                    text_low = text.lower()
                    return [cast_unicode_py2(r) for r in res if r.lower().startswith(text_low)]
            except TryNext:
                pass

        return None

    def complete(self, text=None, line_buffer=None, cursor_pos=None):
        """Find completions for the given text and line context.

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
        # if the cursor position isn't given, the only sane assumption we can
        # make is that it's at the end of the line (the common case)
        if cursor_pos is None:
            cursor_pos = len(line_buffer) if text is None else len(text)

        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if PY3 and self.backslash_combining_completions:

            base_text = text if not line_buffer else line_buffer[:cursor_pos]
            latex_text, latex_matches = self.latex_matches(base_text)
            if latex_matches:
                return latex_text, latex_matches
            name_text = ''
            name_matches = []
            for meth in (self.unicode_name_matches, back_latex_name_matches, back_unicode_name_matches):
                name_text, name_matches = meth(base_text)
                if name_text:
                    return name_text, name_matches
        
        # if text is either None or an empty string, rely on the line buffer
        if not text:
            text = self.splitter.split_line(line_buffer, cursor_pos)

        # If no line buffer is given, assume the input text is all there was
        if line_buffer is None:
            line_buffer = text

        self.line_buffer = line_buffer
        self.text_until_cursor = self.line_buffer[:cursor_pos]

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
        self.matches = sorted(set(self.matches), key=completions_sorting_key)

        return text, self.matches
