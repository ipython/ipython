"""Completion for IPython.

This module now support a wide variety of completion mechanism both available
for normal classic Python code, as well as completer for IPython specific
Syntax like magics.

Starting with IPython 8.0, this module make use of the Jedi library to
generate completions both using static analysis of the code, and dynamically
inspecting multiple namespaces. Jedi is an autocompletion and static analysis
for Python.

We welcome any feedback on these new API, and we also encourage you to try this
module in debug mode (start IPython with ``--Completer.debug=True``) in order
to have extra logging information if :any:`jedi` is crashing, or if current
IPython completer pending deprecations are returning results not yet handled
by :any:`jedi`

Using Jedi for tab completion allow snippets like the following to work without
having to execute any code:

   >>> myvar = ['hello', 42]
   ... myvar[1].bi<tab>

Tab completion will be able to infer that ``myvar[1]`` is a real number without
executing any code unlike the previously available ``IPCompleter.greedy``
option.

Be sure to update :any:`jedi` to the latest stable version or to try the
current development version to get better completions.

Latex and Unicode completion
============================

IPython and compatible frontends not only can complete your code, but can help
you to input a wide range of characters. In particular we allow you to insert
a unicode character using the tab completion mechanism.

Forward latex/unicode completion
--------------------------------

Forward completion allows you to easily type a unicode character using its latex
name, or unicode long description. To do so type a backslash follow by the
relevant name and press tab:


Using latex completion:

.. code::

    \\alpha<tab>
    α

or using unicode completion:


.. code::

    \\GREEK SMALL LETTER ALPHA<tab>
    α


Only valid Python identifiers will complete. Combining characters (like arrow or
dots) are also available, unlike latex they need to be put after the their
counterpart that is to say, `F\\\\vec<tab>` is correct, not `\\\\vec<tab>F`.

Some browsers are known to display combining characters incorrectly.

Backward latex completion
-------------------------

It is sometime challenging to know how to type a character, if you are using
IPython, or any compatible frontend you can prepend backslash to the character
and press `<tab>` to expand it to its latex form.

.. code::

    \\α<tab>
    \\alpha


Both forward and backward completions can be deactivated by setting the
``Completer.backslash_combining_completions`` option to ``False``.
"""


# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Some of this code originated from rlcompleter in the Python standard library
# Copyright (C) 2001 Python Software Foundation, www.python.org


import builtins as builtin_mod
import glob
import inspect
import itertools
import keyword
import os
import re
import string
import sys
import time
import unicodedata
import uuid
import warnings

from collections import defaultdict
from contextlib import contextmanager
from importlib import import_module
from types import SimpleNamespace
from typing import Iterable, Iterator, List, Tuple, Union, Any, Sequence, Dict, NamedTuple, Pattern, Optional

from IPython.core.error import TryNext
from IPython.core.inputtransformer2 import ESC_MAGIC
from IPython.core.latex_symbols import latex_symbols, reverse_latex_symbol
from IPython.core.oinspect import InspectColors
from IPython.utils import generics
from IPython.utils.dir2 import dir2, get_real_method
from IPython.utils.path import ensure_dir_exists
from IPython.utils.process import arg_split
from traitlets import Bool, Enum, Int, List as ListTrait, Unicode, default, observe
from traitlets.config.configurable import Configurable

import __main__

# skip module docstests
skip_doctest = True

import jedi

jedi.settings.case_insensitive_completion = False
import jedi.api.helpers
import jedi.api.classes

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# ranges where we have most of the valid unicode names. We could be more finer
# grained but is it worth it for performace  While unicode have character in the
# rage 0, 0x110000, we seem to have name for about 10% of those. (131808 as I
# write this). With below range we cover them all, with a density of ~67%
# biggest next gap we consider only adds up about 1% density and there are 600
# gaps that would need hard coding.
_UNICODE_RANGES = [(32, 0x3134b), (0xe0001, 0xe01f0)]

# Public API
__all__ = ['Completer','IPCompleter']

if sys.platform == 'win32':
    PROTECTABLES = ' '
else:
    PROTECTABLES = ' ()[]{}?=\\|;:\'#*"^&'

# Protect against returning an enormous number of completions which the frontend
# may have trouble processing.
MATCHES_LIMIT = 500

_deprecation_readline_sentinel = object()


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


def protect_filename(s, protectables=PROTECTABLES):
    """Escape a string to protect certain characters."""
    if set(s) & set(protectables):
        if sys.platform == "win32":
            return '"' + s + '"'
        else:
            return "".join(("\\" + c if c in protectables else c) for c in s)
    else:
        return s


def expand_user(path:str) -> Tuple[str, bool, str]:
    """Expand ``~``-style usernames in strings.

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


def compress_user(path:str, tilde_expand:bool, tilde_val:str) -> str:
    """Does the opposite of expand_user, with its outputs.
    """
    if tilde_expand:
        return path.replace(tilde_val, '~')
    else:
        return path


def completions_sorting_key(word):
    """key for sorting completions

    This does several things:

    - Demote any completions starting with underscores to the end
    - Insert any %magic and %%cellmagic completions in the alphabetical order
      by their name
    """
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

    return (prio1, prio2), word


class _FakeJediCompletion:
    """
    This is a workaround to communicate to the UI that Jedi has crashed and to
    report a bug. Will be used only id :any:`IPCompleter.debug` is set to true.

    Added in IPython 6.0 so should likely be removed for 7.0

    """

    def __init__(self, name):

        self.name = name
        self.complete = name
        self.type = 'crashed'
        self.name_with_symbols = name
        self.signature = ''
        self._origin = 'fake'

    def __repr__(self):
        return '<Fake completion object jedi has crashed>'


class Completion:
    """
    Completion object used and return by IPython completers.

    .. warning::

        Unstable

        This function is unstable, API may change without warning.
        It will also raise unless use in proper context manager.

    This act as a middle ground :any:`Completion` object between the
    :any:`jedi.api.classes.Completion` object and the Prompt Toolkit completion
    object. While Jedi need a lot of information about evaluator and how the
    code should be ran/inspected, PromptToolkit (and other frontend) mostly
    need user facing information.

    - Which range should be replaced replaced by what.
    - Some metadata (like completion type), or meta information to displayed to
      the use user.

    For debugging purpose we can also store the origin of the completion (``jedi``,
    ``IPython.python_matches``, ``IPython.magics_matches``...).
    """

    __slots__ = ['start', 'end', 'text', 'type', 'signature', '_origin']

    def __init__(self, start: int, end: int, text: str, *, type: str=None, _origin='', signature='') -> None:
        self.start = start
        self.end = end
        self.text = text
        self.type = type
        self.signature = signature
        self._origin = _origin

    def __repr__(self):
        return '<Completion start=%s end=%s text=%r type=%r, signature=%r,>' % \
                (self.start, self.end, self.text, self.type or '?', self.signature or '?')

    def __eq__(self, other)->Bool:
        """
        Equality and hash do not hash the type (as some completer may not be
        able to infer the type), but are use to (partially) de-duplicate
        completion.

        Completely de-duplicating completion is a bit tricker that just
        comparing as it depends on surrounding text, which Completions are not
        aware of.
        """
        return self.start == other.start and \
            self.end == other.end and \
            self.text == other.text

    def __hash__(self):
        return hash((self.start, self.end, self.text))


_IC = Iterable[Completion]


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
    setting the ``delims`` attribute (this is a property that internally
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

    jedi_compute_type_timeout = Int(default_value=400,
        help="""Experimental: restrict time (in milliseconds) during which Jedi can compute types.
        Set to 0 to stop computing types. Non-zero value lower than 100ms may hurt
        performance by preventing jedi to build its cache.
        """).tag(config=True)

    debug = Bool(default_value=False,
                 help='Enable debug for the Completer. Mostly print extra '
                      'information for experimental jedi integration.')\
                      .tag(config=True)

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
        """

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = True
        else:
            self.use_main_ns = False
            self.namespace = namespace

        # The global namespace, if given, can be bound directly
        if global_namespace is None:
            self.global_namespace = {}
        else:
            self.global_namespace = global_namespace

        self.custom_matchers = []

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

        snake_case_re = re.compile(r"[^_]+(_[^_]+)+?\Z")
        for lst in [self.namespace.keys(),
                    self.global_namespace.keys()]:
            shortened = {"_".join([sub[0] for sub in word.split('_')]) : word
                         for word in lst if snake_case_re.match(word)}
            for word in shortened.keys():
                if word[:n] == text and word != "__builtins__":
                    match_append(shortened[word])
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluatable in self.namespace or self.global_namespace, it will be
        evaluated and its attributes (as revealed by dir()) are used as
        possible completions.  (For class instances, class members are
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
        except AssertionError:
            raise
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

    return [w for w in words if isinstance(w, str)]


def cursor_to_position(text:str, line:int, column:int)->int:
    """
    Convert the (line,column) position of the cursor in text to an offset in a
    string.

    Parameters
    ----------
    text : str
        The text in which to calculate the cursor offset
    line : int
        Line of the cursor; 0-indexed
    column : int
        Column of the cursor 0-indexed

    Returns
    -------
    Position of the cursor in ``text``, 0-indexed.

    See Also
    --------
    position_to_cursor : reciprocal of this function

    """
    lines = text.split('\n')
    assert line <= len(lines), '{} <= {}'.format(str(line), str(len(lines)))

    return sum(len(l) + 1 for l in lines[:line]) + column

def position_to_cursor(text:str, offset:int)->Tuple[int, int]:
    """
    Convert the position of the cursor in text (0 indexed) to a line
    number(0-indexed) and a column number (0-indexed) pair

    Position should be a valid position in ``text``.

    Parameters
    ----------
    text : str
        The text in which to calculate the cursor offset
    offset : int
        Position of the cursor in ``text``, 0-indexed.

    Returns
    -------
    (line, column) : (int, int)
        Line of the cursor; 0-indexed, column of the cursor 0-indexed

    See Also
    --------
    cursor_to_position : reciprocal of this function

    """

    assert 0 <= offset <= len(text) , "0 <= %s <= %s" % (offset , len(text))

    before = text[:offset]
    blines = before.split('\n')  # ! splitnes trim trailing \n
    line = before.count('\n')
    col = len(blines[-1])
    return line, col


def _safe_isinstance(obj, module, class_name):
    """Checks if obj is an instance of module.class_name if loaded
    """
    return (module in sys.modules and
            isinstance(obj, getattr(import_module(module), class_name)))

def back_unicode_name_matches(text:str) -> Tuple[str, Sequence[str]]:
    """Match Unicode characters back to Unicode name

    This does  ``☃`` -> ``\\snowman``

    Note that snowman is not a valid python3 combining character but will be expanded.
    Though it will not recombine back to the snowman character by the completion machinery.

    This will not either back-complete standard sequences like \\n, \\b ...

    Returns
    =======

    Return a tuple with two elements:

    - The Unicode character that was matched (preceded with a backslash), or
        empty string,
    - a sequence (of 1), name for the match Unicode character, preceded by
        backslash, or empty if no match.

    """
    if len(text)<2:
        return '', ()
    maybe_slash = text[-2]
    if maybe_slash != '\\':
        return '', ()

    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ('"',"'"):
        return '', ()
    try :
        unic = unicodedata.name(char)
        return '\\'+char,('\\'+unic,)
    except KeyError:
        pass
    return '', ()

def back_latex_name_matches(text:str) -> Tuple[str, Sequence[str]] :
    """Match latex characters back to unicode name

    This does ``\\ℵ`` -> ``\\aleph``

    """
    if len(text)<2:
        return '', ()
    maybe_slash = text[-2]
    if maybe_slash != '\\':
        return '', ()


    char = text[-1]
    # no expand on quote for completion in strings.
    # nor backcomplete standard ascii keys
    if char in string.ascii_letters or char in ('"',"'"):
        return '', ()
    try :
        latex = reverse_latex_symbol[char]
        # '\\' replace the \ as well
        return '\\'+char,[latex]
    except KeyError:
        pass
    return '', ()


class IPCompleter(Completer):
    """Extension of the completer class with IPython-specific features"""

    __dict_key_regexps: Optional[Dict[bool,Pattern]] = None

    @observe('greedy')
    def _greedy_changed(self, change):
        """update the splitter and readline delims when greedy is changed"""
        if change['new']:
            self.splitter.delims = GREEDY_DELIMS
        else:
            self.splitter.delims = DELIMS

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

    profile_completions = Bool(
        default_value=False,
        help="If True, emit profiling data for completion subsystem using cProfile."
    ).tag(config=True)

    profiler_output_dir = Unicode(
        default_value=".completion_profiles",
        help="Template for path at which to output profile data for completions."
    ).tag(config=True)

    @observe('limit_to__all__')
    def _limit_to_all_changed(self, change):
        warnings.warn('`IPython.core.IPCompleter.limit_to__all__` configuration '
            'value has been deprecated since IPython 5.0, will be made to have '
            'no effects and then removed in future version of IPython.',
            UserWarning)

    def __init__(self, shell=None, namespace=None, global_namespace=None,
                 use_readline=_deprecation_readline_sentinel, config=None, **kwargs):
        """IPCompleter() -> completer

        Return a completer object.

        Parameters
        ----------
        shell
            a pointer to the ipython shell itself.  This is needed
            because this completer knows about magic functions, and those can
            only be accessed via the ipython instance.
        namespace : dict, optional
            an optional dict where completions are performed.
        global_namespace : dict, optional
            secondary optional dict for completions, to
            handle cases (such as IPython embedded inside functions) where
            both Python scopes are visible.
        use_readline : bool, optional
            DEPRECATED, ignored since IPython 6.0, will have no effects
        """

        self.magic_escape = ESC_MAGIC
        self.splitter = CompletionSplitter()

        if use_readline is not _deprecation_readline_sentinel:
            warnings.warn('The `use_readline` parameter is deprecated and ignored since IPython 6.0.',
                          DeprecationWarning, stacklevel=2)

        # _greedy_changed() depends on splitter and readline being defined:
        Completer.__init__(self, namespace=namespace, global_namespace=global_namespace,
                            config=config, **kwargs)

        # List where completion matches will be stored
        self.matches = []
        self.shell = shell
        # Regexp to split filenames with spaces in them
        self.space_name_re = re.compile(r'([^\\] )')

        # Determine if we are running on 'dumb' terminals, like (X)Emacs
        # buffers, to avoid completion problems.
        term = os.environ.get('TERM','xterm')
        self.dumb_terminal = term in ['dumb','emacs']

        #regexp to parse docstring for function signature
        self.docstring_sig_re = re.compile(r'^[\w|\s.]+\(([^)]*)\).*')
        self.docstring_kwd_re = re.compile(r'[\s|\[]*(\w+)(?:\s*=\s*.*)')
        #use this if positional argument name is also needed
        #= re.compile(r'[\s|\[]*(\w+)(?:\s*=?\s*.*)')

        # This is set externally by InteractiveShell
        self.custom_completers = None

        # This is a list of names of unicode characters that can be completed
        # into their corresponding unicode value. The list is large, so we
        # laziliy initialize it on first use. Consuming code should access this
        # attribute through the `@unicode_names` property.
        self._unicode_names = None

    @property
    def matchers(self) -> List[Any]:
        """All active matcher routines for completion"""
        return [
            *self.custom_matchers,
            self.unicode_matches,
            self.magic_config_matches,
            self.magic_color_matches,
            self.magic_matches,
        ]

    def all_completions(self, text:str) -> List[str]:
        """
        Wrapper around the completion methods for the benefit of emacs.
        """
        prefix = text.rpartition('.')[0]
        return [
            ".".join([prefix, c.text]) if prefix else c.text
            for c in self.completions(text, len(text))
        ]

    def unicode_matches(self, text: str):
        res = []
        if self.backslash_combining_completions:
            # allow deactivation of these on windows.
            latex_text, latex_matches = self.latex_matches(text)
            if latex_matches:
                for m in latex_matches:
                    res.append((latex_text, m, "latex_matches"))
                return res, 2, bool(res)
            name_text = ""
            name_matches = []
            # need to add self.fwd_unicode_match() function here when done
            for meth in (
                self.unicode_name_matches,
                back_latex_name_matches,
                back_unicode_name_matches,
                self.fwd_unicode_match,
            ):
                name_text, name_matches = meth(text)
                if name_text:
                    for m in name_matches[:MATCHES_LIMIT]:
                        res.append((name_text, m, meth.__qualname__))
        return res, 2, bool(res)

    def magic_matches(self, text:str):
        """Match magics"""
        # Get all shell magics now rather than statically, so magics loaded at
        # runtime show up too.
        lsm = self.shell.magics_manager.lsmagic()
        line_magics = lsm['line']
        cell_magics = lsm['cell']
        pre = self.magic_escape
        pre2 = pre+pre

        explicit_magic = text.startswith(pre)

        # Completion logic:
        # - user gives %%: only do cell magics
        # - user gives %: do both line and cell magics
        # - no prefix: do both
        # In other words, line magics are skipped if the user gives %% explicitly
        #
        # We also exclude magics that match any currently visible names:
        # https://github.com/ipython/ipython/issues/4877, unless the user has
        # typed a %:
        # https://github.com/ipython/ipython/issues/10754
        bare_text = text.lstrip(pre)
        global_matches = self.global_matches(bare_text)
        priority = 0
        if not explicit_magic:
            def matches(magic):
                """
                Filter magics, in particular remove magics that match
                a name present in global namespace.
                """
                return ( magic.startswith(bare_text) and
                         magic not in global_matches )
        else:
            priority = 2

            def matches(magic):
                return magic.startswith(bare_text)

        comp = [ pre2+m for m in cell_magics if matches(m)]
        if not text.startswith(pre2):
            comp += [ pre+m for m in line_magics if matches(m)]

        return comp, priority, bool(comp) and explicit_magic

    def magic_config_matches(self, text:str) -> List[str]:
        """ Match class names and attributes for %config magic """
        texts = self.line_buffer.strip().split()

        if len(texts) > 0 and (texts[0] == 'config' or texts[0] == '%config'):
            # get all configuration classes
            classes = sorted(set([ c for c in self.shell.configurables
                                   if c.__class__.class_traits(config=True)
                                   ]), key=lambda x: x.__class__.__name__)
            classnames = [ c.__class__.__name__ for c in classes ]

            # return all classnames if config or %config is given
            if len(texts) == 1:
                return [("", x, "config") for x in classnames], 2, True
            elif len(texts) == 2 and text == "":
                return [("", "=", "config")], 2, True
            elif len(texts) >= 3:
                return [], 2, True

            # match classname
            classname_texts = texts[1].split('.')
            classname = classname_texts[0]
            classname_matches = [ c for c in classnames
                                  if c.startswith(classname) ]

            # return matched classes or the matched class with attributes
            if texts[1].find(".") < 0:
                return [(texts[1], c, "config") for c in classname_matches], 2, True
            elif len(classname_matches) == 1 and classname_matches[0] == classname:
                cls = classes[classnames.index(classname)].__class__
                help = cls.class_get_help()
                # strip leading '--' from cl-args:
                help = re.sub(re.compile(r"^--", re.MULTILINE), "", help)
                return (
                    [
                        (texts[1], attr.split("=")[0], "config")
                        for attr in help.strip().splitlines()
                        if attr.startswith(texts[1])
                    ],
                    2,
                    True,
                )
        return [], 0, False

    def magic_color_matches(self, text:str) -> List[str] :
        """ Match color schemes for %colors magic"""
        texts = self.line_buffer.strip().split()

        if len(texts) == 1 and (texts[0] == "colors" or texts[0] == "%colors"):
            return (
                [color for color in InspectColors.keys() if color.startswith(text)],
                2,
                True,
            )
        return [], 0, False

    def _jedi_matches(
        self, offset: int, cursor_line: int, cursor_column: int, text: str
    ) -> Iterable[Any]:
        """
        Return a list of :any:`jedi.api.Completions` object from a ``text`` and
        cursor position.

        Parameters
        ----------
        text:str
            text to complete

        Notes
        -----
        If ``IPCompleter.debug`` is ``True`` may return a :any:`_FakeJediCompletion`
        object containing a string with the Jedi debug information attached.
        """
        namespaces = [self.namespace]
        if self.global_namespace is not None:
            namespaces.append(self.global_namespace)

        completion_filter = lambda x:x
        # filter output if we are completing for object members
        pre = text[-1]
        if pre == ".":
            if self.omit__names == 2:
                completion_filter = lambda c: not c.name.startswith("_")
            elif self.omit__names == 1:
                completion_filter = lambda c: not (
                    c.name.startswith("__") and c.name.endswith("__")
                )
            elif self.omit__names == 0:
                completion_filter = lambda x: x
            else:
                raise ValueError(
                    "Don't understand self.omit__names == {}".format(self.omit__names)
                )

        interpreter = jedi.Interpreter(text, namespaces)

        try:
            return filter(completion_filter, interpreter.complete(column=cursor_column, line=cursor_line + 1))
        except Exception as e:
            # I think that even end-users should be aware
            # of jedi failures (previously only in debug).
            # For instance, to detect Access Denied errors
            return [
                _FakeJediCompletion(
                    'Oops Jedi has crashed, please report a bug with the following:\n"""\n%s\ns"""'
                    % (e)
                )
            ]

    @staticmethod
    def unicode_name_matches(text:str) -> Tuple[str, List[str]] :
        """Match Latex-like syntax for unicode characters base
        on the name of the character.

        This does  ``\\GREEK SMALL LETTER ETA`` -> ``η``

        Works only on valid python 3 identifier, or on combining characters that
        will combine to form a valid identifier.
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
        return '', []


    def latex_matches(self, text:str) -> Tuple[str, Sequence[str]]:
        """Match Latex syntax for unicode characters.

        This does both ``\\alp`` -> ``\\alpha`` and ``\\alpha`` -> ``α``
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
                if matches:
                    return s, matches
        return '', ()

    def dispatch_custom_completer(self, text):
        if not self.custom_completers:
            return

        line = self.line_buffer
        if not line.strip():
            return None

        # Create a little structure to pass all the relevant information about
        # the current completion to any custom completer.
        event = SimpleNamespace()
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
                    withcase = [r for r in res if r.startswith(text)]
                    if withcase:
                        return withcase
                    # if none, then case insensitive ones are ok too
                    text_low = text.lower()
                    return [r for r in res if r.lower().startswith(text_low)]
            except TryNext:
                pass
            except KeyboardInterrupt:
                """
                If custom completer take too long,
                let keyboard interrupt abort and return nothing.
                """
                break

        return None

    def completions(self, text: str, offset: int)->Iterator[Completion]:
        """
        Returns an iterator over the possible completions

        .. warning::

            Unstable

            This function is unstable, API may change without warning.
            It will also raise unless use in proper context manager.

        Parameters
        ----------
        text : str
            Full text of the current input, multi line string.
        offset : int
            Integer representing the position of the cursor in ``text``. Offset
            is 0-based indexed.

        Yields
        ------
        Completion

        Notes
        -----
        The cursor on a text can either be seen as being "in between"
        characters or "On" a character depending on the interface visible to
        the user. For consistency the cursor being on "in between" characters X
        and Y is equivalent to the cursor being "on" character Y, that is to say
        the character the cursor is on is considered as being after the cursor.

        Combining characters may span more that one position in the
        text.

        .. note::

            If ``IPCompleter.debug`` is :any:`True` will yield a ``--jedi/ipython--``
            fake Completion token to distinguish completion returned by Jedi
            and usual IPython completion.

        .. note::

            Completions are not completely deduplicated yet. If identical
            completions are coming from different sources this function does not
            ensure that each completion object will only be present once.
        """

        seen = set()
        profiler:Optional[cProfile.Profile]
        try:
            if self.profile_completions:
                import cProfile
                profiler = cProfile.Profile()
                profiler.enable()
            else:
                profiler = None

            for c in self._completions(text, offset, _timeout=self.jedi_compute_type_timeout/1000):
                if c and (c in seen):
                    continue
                yield c
                seen.add(c)
        except KeyboardInterrupt:
            """if completions take too long and users send keyboard interrupt,
            do not crash and return ASAP. """
            pass
        finally:
            if profiler is not None:
                profiler.disable()
                ensure_dir_exists(self.profiler_output_dir)
                output_path = os.path.join(self.profiler_output_dir, str(uuid.uuid4()))
                print("Writing profiler output to", output_path)
                profiler.dump_stats(output_path)

    def _completions(self, full_text: str, offset: int, *, _timeout) -> Iterator[Completion]:
        """
        Core completion module.Same signature as :any:`completions`, with the
        extra `timeout` parameter (in seconds).

        Computing jedi's completion ``.type`` can be quite expensive (it is a
        lazy property) and can require some warm-up, more warm up than just
        computing the ``name`` of a completion. The warm-up can be :

            - Long warm-up the first time a module is encountered after
            install/update: actually build parse/inference tree.

            - first time the module is encountered in a session: load tree from
            disk.

        We don't want to block completions for tens of seconds so we give the
        completer a "budget" of ``_timeout`` seconds per invocation to compute
        completions types, the completions that have not yet been computed will
        be marked as "unknown" an will have a chance to be computed next round
        are things get cached.

        Keep in mind that Jedi is not the only thing treating the completion so
        keep the timeout short-ish as if we take more than 0.3 second we still
        have lots of processing to do.

        """
        deadline = time.monotonic() + _timeout

        cursor_line, cursor_column = position_to_cursor(full_text, offset)
        self.line_buffer = full_text.split("\n")[cursor_line]
        self.text_until_cursor = self.line_buffer[:cursor_column]

        if self.use_main_ns:
            self.namespace = __main__.__dict__

        iterators = defaultdict(list)

        text = self.splitter.split_line(self.line_buffer)

        # Dispatch special completions
        for matcher in self.matchers:
            try:
                results = matcher(text)
                if isinstance(results, tuple):
                    matches, priority, alone = results
                else:
                    matches, priority, alone = results, 2, False

                def iter_matches(matches=matches):
                    for m in matches:
                        if isinstance(m, tuple):
                            t, m, o = m
                        else:
                            o = matcher.__qualname__
                            t = text
                        delta = len(t)
                        yield Completion(
                            start=cursor_column - delta,
                            end=cursor_column,
                            text=m,
                            type="",
                            _origin=o,
                            signature="",
                        )

                iterators[priority].append(iter_matches)
                if alone:
                    break
            except:
                # Show the ugly traceback if the matcher causes an
                # exception, but do NOT crash the kernel!
                sys.excepthook(*sys.exc_info())
        else:
            # Dispatch jedi completion
            jedi_matches = self._jedi_matches(
                offset, cursor_line, cursor_column, full_text
            )

            def iter_jedi(jedi_matches=jedi_matches):
                for jm in iter(jedi_matches):
                    delta = len(jm.name_with_symbols) - len(jm.complete)
                    yield Completion(
                        start=cursor_column - delta,
                        end=cursor_column,
                        text=jm.name_with_symbols,
                        type=jm.type,
                        _origin="jedi",
                        signature="",
                    )
                    # Check for timeout
                    if _timeout and time.monotonic() > deadline:
                        break

            iterators[1].append(iter_jedi)

        # Generate results
        for cmpl_l in sorted(iterators.items(), reverse=True):
            for cmpl in cmpl_l[1]:
                for completion in cmpl():
                    yield completion

    def fwd_unicode_match(self, text: str) -> Tuple[str, list]:
        slashpos = text.rfind("\\")
        # if text starts with slash
        if slashpos > -1:
            s = text[slashpos + 1 :]
            # PERF: It's important that we don't access self._unicode_names
            # until we're inside this if-block. _unicode_names is lazily
            # initialized, and it takes a user-noticeable amount of time to
            # initialize it, so we don't want to initialize it unless we're
            # actually going to use it.
            s = text[slashpos+1:]
            candidates = [x for x in self.unicode_names if x.startswith(s)]
            if candidates:
                return s, candidates
        return "", ()

    @property
    def unicode_names(self) -> List[str]:
        """List of names of unicode code points that can be completed.
        The list is lazily initialized on first access.
        """
        if self._unicode_names is None:
            names = []
            for c in range(0,0x10FFFF + 1):
                try:
                    names.append(unicodedata.name(chr(c)))
                except ValueError:
                    pass
            self._unicode_names = _unicode_name_compute(_UNICODE_RANGES)

        return self._unicode_names

def _unicode_name_compute(ranges:List[Tuple[int,int]]) -> List[str]:
    names = []
    for start,stop in ranges:
        for c in range(start, stop) :
            try:
                names.append(unicodedata.name(chr(c)))
            except ValueError:
                pass
    return names
