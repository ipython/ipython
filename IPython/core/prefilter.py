# encoding: utf-8
"""
Prefiltering components.

Prefilters transform user input before it is exec'd by Python.  These
transforms are used to implement additional syntax such as !ls and %magic.

Authors:

* Brian Granger
* Fernando Perez
* Dan Milstein
* Ville Vainio
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import codeop
import re

from IPython.core.alias import AliasManager
from IPython.core.autocall import IPyAutocall
from IPython.config.configurable import Configurable
from IPython.core.inputsplitter import (
    ESC_SHELL,
    ESC_SH_CAP,
    ESC_HELP,
    ESC_MAGIC,
    ESC_MAGIC2,
    ESC_QUOTE,
    ESC_QUOTE2,
    ESC_PAREN,
)
from IPython.core.macro import Macro
from IPython.core.splitinput import split_user_input, LineInfo
from IPython.core import page

from IPython.utils.traitlets import (
    List, Integer, Any, Unicode, CBool, Bool, Instance, CRegExp
)
from IPython.utils.autoattr import auto_attr

#-----------------------------------------------------------------------------
# Global utilities, errors and constants
#-----------------------------------------------------------------------------


class PrefilterError(Exception):
    pass


# RegExp to identify potential function names
re_fun_name = re.compile(r'[a-zA-Z_]([a-zA-Z0-9_.]*) *$')

# RegExp to exclude strings with this start from autocalling.  In
# particular, all binary operators should be excluded, so that if foo is
# callable, foo OP bar doesn't become foo(OP bar), which is invalid.  The
# characters '!=()' don't need to be checked for, as the checkPythonChars
# routine explicitely does so, to catch direct calls and rebindings of
# existing names.

# Warning: the '-' HAS TO BE AT THE END of the first group, otherwise
# it affects the rest of the group in square brackets.
re_exclude_auto = re.compile(r'^[,&^\|\*/\+-]'
                             r'|^is |^not |^in |^and |^or ')

# try to catch also methods for stuff in lists/tuples/dicts: off
# (experimental). For this to work, the line_split regexp would need
# to be modified so it wouldn't break things at '['. That line is
# nasty enough that I shouldn't change it until I can test it _well_.
#self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')


# Handler Check Utilities
def is_shadowed(identifier, ip):
    """Is the given identifier defined in one of the namespaces which shadow
    the alias and magic namespaces?  Note that an identifier is different
    than ifun, because it can not contain a '.' character."""
    # This is much safer than calling ofind, which can change state
    return (identifier in ip.user_ns \
            or identifier in ip.user_global_ns \
            or identifier in ip.ns_table['builtin'])


#-----------------------------------------------------------------------------
# Main Prefilter manager
#-----------------------------------------------------------------------------


class PrefilterManager(Configurable):
    """Main prefilter component.

    The IPython prefilter is run on all user input before it is run.  The
    prefilter consumes lines of input and produces transformed lines of
    input.

    The iplementation consists of two phases:

    1. Transformers
    2. Checkers and handlers

    Over time, we plan on deprecating the checkers and handlers and doing
    everything in the transformers.

    The transformers are instances of :class:`PrefilterTransformer` and have
    a single method :meth:`transform` that takes a line and returns a
    transformed line.  The transformation can be accomplished using any
    tool, but our current ones use regular expressions for speed.

    After all the transformers have been run, the line is fed to the checkers,
    which are instances of :class:`PrefilterChecker`.  The line is passed to
    the :meth:`check` method, which either returns `None` or a
    :class:`PrefilterHandler` instance.  If `None` is returned, the other
    checkers are tried.  If an :class:`PrefilterHandler` instance is returned,
    the line is passed to the :meth:`handle` method of the returned
    handler and no further checkers are tried.

    Both transformers and checkers have a `priority` attribute, that determines
    the order in which they are called.  Smaller priorities are tried first.

    Both transformers and checkers also have `enabled` attribute, which is
    a boolean that determines if the instance is used.

    Users or developers can change the priority or enabled attribute of
    transformers or checkers, but they must call the :meth:`sort_checkers`
    or :meth:`sort_transformers` method after changing the priority.
    """

    multi_line_specials = CBool(True, config=True)
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None, config=None):
        super(PrefilterManager, self).__init__(shell=shell, config=config)
        self.shell = shell
        self.init_transformers()
        self.init_handlers()
        self.init_checkers()

    #-------------------------------------------------------------------------
    # API for managing transformers
    #-------------------------------------------------------------------------

    def init_transformers(self):
        """Create the default transformers."""
        self._transformers = []
        for transformer_cls in _default_transformers:
            transformer_cls(
                shell=self.shell, prefilter_manager=self, config=self.config
            )

    def sort_transformers(self):
        """Sort the transformers by priority.

        This must be called after the priority of a transformer is changed.
        The :meth:`register_transformer` method calls this automatically.
        """
        self._transformers.sort(key=lambda x: x.priority)

    @property
    def transformers(self):
        """Return a list of checkers, sorted by priority."""
        return self._transformers

    def register_transformer(self, transformer):
        """Register a transformer instance."""
        if transformer not in self._transformers:
            self._transformers.append(transformer)
            self.sort_transformers()

    def unregister_transformer(self, transformer):
        """Unregister a transformer instance."""
        if transformer in self._transformers:
            self._transformers.remove(transformer)

    #-------------------------------------------------------------------------
    # API for managing checkers
    #-------------------------------------------------------------------------

    def init_checkers(self):
        """Create the default checkers."""
        self._checkers = []
        for checker in _default_checkers:
            checker(
                shell=self.shell, prefilter_manager=self, config=self.config
            )

    def sort_checkers(self):
        """Sort the checkers by priority.

        This must be called after the priority of a checker is changed.
        The :meth:`register_checker` method calls this automatically.
        """
        self._checkers.sort(key=lambda x: x.priority)

    @property
    def checkers(self):
        """Return a list of checkers, sorted by priority."""
        return self._checkers

    def register_checker(self, checker):
        """Register a checker instance."""
        if checker not in self._checkers:
            self._checkers.append(checker)
            self.sort_checkers()

    def unregister_checker(self, checker):
        """Unregister a checker instance."""
        if checker in self._checkers:
            self._checkers.remove(checker)

    #-------------------------------------------------------------------------
    # API for managing checkers
    #-------------------------------------------------------------------------

    def init_handlers(self):
        """Create the default handlers."""
        self._handlers = {}
        self._esc_handlers = {}
        for handler in _default_handlers:
            handler(
                shell=self.shell, prefilter_manager=self, config=self.config
            )

    @property
    def handlers(self):
        """Return a dict of all the handlers."""
        return self._handlers

    def register_handler(self, name, handler, esc_strings):
        """Register a handler instance by name with esc_strings."""
        self._handlers[name] = handler
        for esc_str in esc_strings:
            self._esc_handlers[esc_str] = handler

    def unregister_handler(self, name, handler, esc_strings):
        """Unregister a handler instance by name with esc_strings."""
        try:
            del self._handlers[name]
        except KeyError:
            pass
        for esc_str in esc_strings:
            h = self._esc_handlers.get(esc_str)
            if h is handler:
                del self._esc_handlers[esc_str]

    def get_handler_by_name(self, name):
        """Get a handler by its name."""
        return self._handlers.get(name)

    def get_handler_by_esc(self, esc_str):
        """Get a handler by its escape string."""
        return self._esc_handlers.get(esc_str)

    #-------------------------------------------------------------------------
    # Main prefiltering API
    #-------------------------------------------------------------------------

    def prefilter_line_info(self, line_info):
        """Prefilter a line that has been converted to a LineInfo object.

        This implements the checker/handler part of the prefilter pipe.
        """
        # print "prefilter_line_info: ", line_info
        handler = self.find_handler(line_info)
        return handler.handle(line_info)

    def find_handler(self, line_info):
        """Find a handler for the line_info by trying checkers."""
        for checker in self.checkers:
            if checker.enabled:
                handler = checker.check(line_info)
                if handler:
                    return handler
        return self.get_handler_by_name('normal')

    def transform_line(self, line, continue_prompt):
        """Calls the enabled transformers in order of increasing priority."""
        for transformer in self.transformers:
            if transformer.enabled:
                line = transformer.transform(line, continue_prompt)
        return line

    def prefilter_line(self, line, continue_prompt=False):
        """Prefilter a single input line as text.

        This method prefilters a single line of text by calling the
        transformers and then the checkers/handlers.
        """

        # print "prefilter_line: ", line, continue_prompt
        # All handlers *must* return a value, even if it's blank ('').

        # save the line away in case we crash, so the post-mortem handler can
        # record it
        self.shell._last_input_line = line

        if not line:
            # Return immediately on purely empty lines, so that if the user
            # previously typed some whitespace that started a continuation
            # prompt, he can break out of that loop with just an empty line.
            # This is how the default python prompt works.
            return ''

        # At this point, we invoke our transformers.
        if not continue_prompt or (continue_prompt and self.multi_line_specials):
            line = self.transform_line(line, continue_prompt)

        # Now we compute line_info for the checkers and handlers
        line_info = LineInfo(line, continue_prompt)

        # the input history needs to track even empty lines
        stripped = line.strip()

        normal_handler = self.get_handler_by_name('normal')
        if not stripped:
            if not continue_prompt:
                self.shell.displayhook.prompt_count -= 1

            return normal_handler.handle(line_info)

        # special handlers are only allowed for single line statements
        if continue_prompt and not self.multi_line_specials:
            return normal_handler.handle(line_info)

        prefiltered = self.prefilter_line_info(line_info)
        # print "prefiltered line: %r" % prefiltered
        return prefiltered

    def prefilter_lines(self, lines, continue_prompt=False):
        """Prefilter multiple input lines of text.

        This is the main entry point for prefiltering multiple lines of
        input.  This simply calls :meth:`prefilter_line` for each line of
        input.

        This covers cases where there are multiple lines in the user entry,
        which is the case when the user goes back to a multiline history
        entry and presses enter.
        """
        llines = lines.rstrip('\n').split('\n')
        # We can get multiple lines in one shot, where multiline input 'blends'
        # into one line, in cases like recalling from the readline history
        # buffer.  We need to make sure that in such cases, we correctly
        # communicate downstream which line is first and which are continuation
        # ones.
        if len(llines) > 1:
            out = '\n'.join([self.prefilter_line(line, lnum>0)
                             for lnum, line in enumerate(llines) ])
        else:
            out = self.prefilter_line(llines[0], continue_prompt)

        return out

#-----------------------------------------------------------------------------
# Prefilter transformers
#-----------------------------------------------------------------------------


class PrefilterTransformer(Configurable):
    """Transform a line of user input."""

    priority = Integer(100, config=True)
    # Transformers don't currently use shell or prefilter_manager, but as we
    # move away from checkers and handlers, they will need them.
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    prefilter_manager = Instance('IPython.core.prefilter.PrefilterManager')
    enabled = Bool(True, config=True)

    def __init__(self, shell=None, prefilter_manager=None, config=None):
        super(PrefilterTransformer, self).__init__(
            shell=shell, prefilter_manager=prefilter_manager, config=config
        )
        self.prefilter_manager.register_transformer(self)

    def transform(self, line, continue_prompt):
        """Transform a line, returning the new one."""
        return None

    def __repr__(self):
        return "<%s(priority=%r, enabled=%r)>" % (
            self.__class__.__name__, self.priority, self.enabled)


_assign_system_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*!(?P<cmd>.*)')


class AssignSystemTransformer(PrefilterTransformer):
    """Handle the `files = !ls` syntax."""

    priority = Integer(100, config=True)

    def transform(self, line, continue_prompt):
        m = _assign_system_re.match(line)
        if m is not None:
            cmd = m.group('cmd')
            lhs = m.group('lhs')
            expr = "sc =%s" % cmd
            new_line = '%s = get_ipython().magic(%r)' % (lhs, expr)
            return new_line
        return line


_assign_magic_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*%(?P<cmd>.*)')

class AssignMagicTransformer(PrefilterTransformer):
    """Handle the `a = %who` syntax."""

    priority = Integer(200, config=True)

    def transform(self, line, continue_prompt):
        m = _assign_magic_re.match(line)
        if m is not None:
            cmd = m.group('cmd')
            lhs = m.group('lhs')
            new_line = '%s = get_ipython().magic(%r)' % (lhs, cmd)
            return new_line
        return line


_classic_prompt_re = re.compile(r'(^[ \t]*>>> |^[ \t]*\.\.\. )')

class PyPromptTransformer(PrefilterTransformer):
    """Handle inputs that start with '>>> ' syntax."""

    priority = Integer(50, config=True)

    def transform(self, line, continue_prompt):

        if not line or line.isspace() or line.strip() == '...':
            # This allows us to recognize multiple input prompts separated by
            # blank lines and pasted in a single chunk, very common when
            # pasting doctests or long tutorial passages.
            return ''
        m = _classic_prompt_re.match(line)
        if m:
            return line[len(m.group(0)):]
        else:
            return line


_ipy_prompt_re = re.compile(r'(^[ \t]*In \[\d+\]: |^[ \t]*\ \ \ \.\.\.+: )')

class IPyPromptTransformer(PrefilterTransformer):
    """Handle inputs that start classic IPython prompt syntax."""

    priority = Integer(50, config=True)

    def transform(self, line, continue_prompt):

        if not line or line.isspace() or line.strip() == '...':
            # This allows us to recognize multiple input prompts separated by
            # blank lines and pasted in a single chunk, very common when
            # pasting doctests or long tutorial passages.
            return ''
        m = _ipy_prompt_re.match(line)
        if m:
            return line[len(m.group(0)):]
        else:
            return line

#-----------------------------------------------------------------------------
# Prefilter checkers
#-----------------------------------------------------------------------------


class PrefilterChecker(Configurable):
    """Inspect an input line and return a handler for that line."""

    priority = Integer(100, config=True)
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    prefilter_manager = Instance('IPython.core.prefilter.PrefilterManager')
    enabled = Bool(True, config=True)

    def __init__(self, shell=None, prefilter_manager=None, config=None):
        super(PrefilterChecker, self).__init__(
            shell=shell, prefilter_manager=prefilter_manager, config=config
        )
        self.prefilter_manager.register_checker(self)

    def check(self, line_info):
        """Inspect line_info and return a handler instance or None."""
        return None

    def __repr__(self):
        return "<%s(priority=%r, enabled=%r)>" % (
            self.__class__.__name__, self.priority, self.enabled)


class EmacsChecker(PrefilterChecker):

    priority = Integer(100, config=True)
    enabled = Bool(False, config=True)

    def check(self, line_info):
        "Emacs ipython-mode tags certain input lines."
        if line_info.line.endswith('# PYTHON-MODE'):
            return self.prefilter_manager.get_handler_by_name('emacs')
        else:
            return None


class ShellEscapeChecker(PrefilterChecker):

    priority = Integer(200, config=True)

    def check(self, line_info):
        if line_info.line.lstrip().startswith(ESC_SHELL):
            return self.prefilter_manager.get_handler_by_name('shell')


class MacroChecker(PrefilterChecker):

    priority = Integer(250, config=True)

    def check(self, line_info):
        obj = self.shell.user_ns.get(line_info.ifun)
        if isinstance(obj, Macro):
            return self.prefilter_manager.get_handler_by_name('macro')
        else:
            return None


class IPyAutocallChecker(PrefilterChecker):

    priority = Integer(300, config=True)

    def check(self, line_info):
        "Instances of IPyAutocall in user_ns get autocalled immediately"
        obj = self.shell.user_ns.get(line_info.ifun, None)
        if isinstance(obj, IPyAutocall):
            obj.set_ip(self.shell)
            return self.prefilter_manager.get_handler_by_name('auto')
        else:
            return None


class MultiLineMagicChecker(PrefilterChecker):

    priority = Integer(400, config=True)

    def check(self, line_info):
        "Allow ! and !! in multi-line statements if multi_line_specials is on"
        # Note that this one of the only places we check the first character of
        # ifun and *not* the pre_char.  Also note that the below test matches
        # both ! and !!.
        if line_info.continue_prompt \
            and self.prefilter_manager.multi_line_specials:
                if line_info.esc == ESC_MAGIC:
                    return self.prefilter_manager.get_handler_by_name('magic')
        else:
            return None


class EscCharsChecker(PrefilterChecker):

    priority = Integer(500, config=True)

    def check(self, line_info):
        """Check for escape character and return either a handler to handle it,
        or None if there is no escape char."""
        if line_info.line[-1] == ESC_HELP \
               and line_info.esc != ESC_SHELL \
               and line_info.esc != ESC_SH_CAP:
            # the ? can be at the end, but *not* for either kind of shell escape,
            # because a ? can be a vaild final char in a shell cmd
            return self.prefilter_manager.get_handler_by_name('help')
        else:
            if line_info.pre:
                return None
            # This returns None like it should if no handler exists
            return self.prefilter_manager.get_handler_by_esc(line_info.esc)


class AssignmentChecker(PrefilterChecker):

    priority = Integer(600, config=True)

    def check(self, line_info):
        """Check to see if user is assigning to a var for the first time, in
        which case we want to avoid any sort of automagic / autocall games.

        This allows users to assign to either alias or magic names true python
        variables (the magic/alias systems always take second seat to true
        python code).  E.g. ls='hi', or ls,that=1,2"""
        if line_info.the_rest:
            if line_info.the_rest[0] in '=,':
                return self.prefilter_manager.get_handler_by_name('normal')
        else:
            return None


class AutoMagicChecker(PrefilterChecker):

    priority = Integer(700, config=True)

    def check(self, line_info):
        """If the ifun is magic, and automagic is on, run it.  Note: normal,
        non-auto magic would already have been triggered via '%' in
        check_esc_chars. This just checks for automagic.  Also, before
        triggering the magic handler, make sure that there is nothing in the
        user namespace which could shadow it."""
        if not self.shell.automagic or not self.shell.find_magic(line_info.ifun):
            return None

        # We have a likely magic method.  Make sure we should actually call it.
        if line_info.continue_prompt and not self.prefilter_manager.multi_line_specials:
            return None

        head = line_info.ifun.split('.',1)[0]
        if is_shadowed(head, self.shell):
            return None

        return self.prefilter_manager.get_handler_by_name('magic')


class AliasChecker(PrefilterChecker):

    priority = Integer(800, config=True)

    def check(self, line_info):
        "Check if the initital identifier on the line is an alias."
        # Note: aliases can not contain '.'
        head = line_info.ifun.split('.',1)[0]
        if line_info.ifun not in self.shell.alias_manager \
               or head not in self.shell.alias_manager \
               or is_shadowed(head, self.shell):
            return None

        return self.prefilter_manager.get_handler_by_name('alias')


class PythonOpsChecker(PrefilterChecker):

    priority = Integer(900, config=True)

    def check(self, line_info):
        """If the 'rest' of the line begins with a function call or pretty much
        any python operator, we should simply execute the line (regardless of
        whether or not there's a possible autocall expansion).  This avoids
        spurious (and very confusing) geattr() accesses."""
        if line_info.the_rest and line_info.the_rest[0] in '!=()<>,+*/%^&|':
            return self.prefilter_manager.get_handler_by_name('normal')
        else:
            return None


class AutocallChecker(PrefilterChecker):

    priority = Integer(1000, config=True)

    function_name_regexp = CRegExp(re_fun_name, config=True,
        help="RegExp to identify potential function names.")
    exclude_regexp = CRegExp(re_exclude_auto, config=True,
        help="RegExp to exclude strings with this start from autocalling.")

    def check(self, line_info):
        "Check if the initial word/function is callable and autocall is on."
        if not self.shell.autocall:
            return None

        oinfo = line_info.ofind(self.shell) # This can mutate state via getattr
        if not oinfo['found']:
            return None

        if callable(oinfo['obj']) \
               and (not self.exclude_regexp.match(line_info.the_rest)) \
               and self.function_name_regexp.match(line_info.ifun):
            return self.prefilter_manager.get_handler_by_name('auto')
        else:
            return None


#-----------------------------------------------------------------------------
# Prefilter handlers
#-----------------------------------------------------------------------------


class PrefilterHandler(Configurable):

    handler_name = Unicode('normal')
    esc_strings = List([])
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    prefilter_manager = Instance('IPython.core.prefilter.PrefilterManager')

    def __init__(self, shell=None, prefilter_manager=None, config=None):
        super(PrefilterHandler, self).__init__(
            shell=shell, prefilter_manager=prefilter_manager, config=config
        )
        self.prefilter_manager.register_handler(
            self.handler_name,
            self,
            self.esc_strings
        )

    def handle(self, line_info):
        # print "normal: ", line_info
        """Handle normal input lines. Use as a template for handlers."""

        # With autoindent on, we need some way to exit the input loop, and I
        # don't want to force the user to have to backspace all the way to
        # clear the line.  The rule will be in this case, that either two
        # lines of pure whitespace in a row, or a line of pure whitespace but
        # of a size different to the indent level, will exit the input loop.
        line = line_info.line
        continue_prompt = line_info.continue_prompt

        if (continue_prompt and
            self.shell.autoindent and
            line.isspace() and
            0 < abs(len(line) - self.shell.indent_current_nsp) <= 2):
            line = ''

        return line

    def __str__(self):
        return "<%s(name=%s)>" % (self.__class__.__name__, self.handler_name)


class AliasHandler(PrefilterHandler):

    handler_name = Unicode('alias')

    def handle(self, line_info):
        """Handle alias input lines. """
        transformed = self.shell.alias_manager.expand_aliases(line_info.ifun,line_info.the_rest)
        # pre is needed, because it carries the leading whitespace.  Otherwise
        # aliases won't work in indented sections.
        line_out = '%sget_ipython().system(%r)' % (line_info.pre_whitespace, transformed)

        return line_out


class ShellEscapeHandler(PrefilterHandler):

    handler_name = Unicode('shell')
    esc_strings = List([ESC_SHELL, ESC_SH_CAP])

    def handle(self, line_info):
        """Execute the line in a shell, empty return value"""
        magic_handler = self.prefilter_manager.get_handler_by_name('magic')

        line = line_info.line
        if line.lstrip().startswith(ESC_SH_CAP):
            # rewrite LineInfo's line, ifun and the_rest to properly hold the
            # call to %sx and the actual command to be executed, so
            # handle_magic can work correctly.  Note that this works even if
            # the line is indented, so it handles multi_line_specials
            # properly.
            new_rest = line.lstrip()[2:]
            line_info.line = '%ssx %s' % (ESC_MAGIC, new_rest)
            line_info.ifun = 'sx'
            line_info.the_rest = new_rest
            return magic_handler.handle(line_info)
        else:
            cmd = line.lstrip().lstrip(ESC_SHELL)
            line_out = '%sget_ipython().system(%r)' % (line_info.pre_whitespace, cmd)
        return line_out


class MacroHandler(PrefilterHandler):
    handler_name = Unicode("macro")

    def handle(self, line_info):
        obj = self.shell.user_ns.get(line_info.ifun)
        pre_space = line_info.pre_whitespace
        line_sep = "\n" + pre_space
        return pre_space + line_sep.join(obj.value.splitlines())


class MagicHandler(PrefilterHandler):

    handler_name = Unicode('magic')
    esc_strings = List([ESC_MAGIC])

    def handle(self, line_info):
        """Execute magic functions."""
        ifun    = line_info.ifun
        the_rest = line_info.the_rest
        cmd = '%sget_ipython().magic(%r)' % (line_info.pre_whitespace,
                                                    (ifun + " " + the_rest))
        return cmd


class AutoHandler(PrefilterHandler):

    handler_name = Unicode('auto')
    esc_strings = List([ESC_PAREN, ESC_QUOTE, ESC_QUOTE2])

    def handle(self, line_info):
        """Handle lines which can be auto-executed, quoting if requested."""
        line    = line_info.line
        ifun    = line_info.ifun
        the_rest = line_info.the_rest
        pre     = line_info.pre
        esc     = line_info.esc
        continue_prompt = line_info.continue_prompt
        obj = line_info.ofind(self.shell)['obj']
        #print 'pre <%s> ifun <%s> rest <%s>' % (pre,ifun,the_rest)  # dbg

        # This should only be active for single-line input!
        if continue_prompt:
            return line

        force_auto = isinstance(obj, IPyAutocall)

        # User objects sometimes raise exceptions on attribute access other
        # than AttributeError (we've seen it in the past), so it's safest to be
        # ultra-conservative here and catch all.
        try:
            auto_rewrite = obj.rewrite
        except Exception:
            auto_rewrite = True

        if esc == ESC_QUOTE:
            # Auto-quote splitting on whitespace
            newcmd = '%s("%s")' % (ifun,'", "'.join(the_rest.split()) )
        elif esc == ESC_QUOTE2:
            # Auto-quote whole string
            newcmd = '%s("%s")' % (ifun,the_rest)
        elif esc == ESC_PAREN:
            newcmd = '%s(%s)' % (ifun,",".join(the_rest.split()))
        else:
            # Auto-paren.       
            if force_auto:
                # Don't rewrite if it is already a call.
                do_rewrite = not the_rest.startswith('(')
            else:
                if not the_rest:
                    # We only apply it to argument-less calls if the autocall
                    # parameter is set to 2.
                    do_rewrite = (self.shell.autocall >= 2)
                elif the_rest.startswith('[') and hasattr(obj, '__getitem__'):
                    # Don't autocall in this case: item access for an object
                    # which is BOTH callable and implements __getitem__.
                    do_rewrite = False
                else:
                    do_rewrite = True

            # Figure out the rewritten command
            if do_rewrite:
                if the_rest.endswith(';'):
                    newcmd = '%s(%s);' % (ifun.rstrip(),the_rest[:-1])
                else:
                    newcmd = '%s(%s)' % (ifun.rstrip(), the_rest)                
            else:
                normal_handler = self.prefilter_manager.get_handler_by_name('normal')
                return normal_handler.handle(line_info)
        
        # Display the rewritten call
        if auto_rewrite:
            self.shell.auto_rewrite_input(newcmd)

        return newcmd


class HelpHandler(PrefilterHandler):

    handler_name = Unicode('help')
    esc_strings = List([ESC_HELP])

    def handle(self, line_info):
        """Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """
        normal_handler = self.prefilter_manager.get_handler_by_name('normal')
        line = line_info.line
        # We need to make sure that we don't process lines which would be
        # otherwise valid python, such as "x=1 # what?"
        try:
            codeop.compile_command(line)
        except SyntaxError:
            # We should only handle as help stuff which is NOT valid syntax
            if line[0]==ESC_HELP:
                line = line[1:]
            elif line[-1]==ESC_HELP:
                line = line[:-1]
            if line:
                #print 'line:<%r>' % line  # dbg
                self.shell.magic('pinfo %s' % line_info.ifun)
            else:
                self.shell.show_usage()
            return '' # Empty string is needed here!
        except:
            raise
            # Pass any other exceptions through to the normal handler
            return normal_handler.handle(line_info)
        else:
            # If the code compiles ok, we should handle it normally
            return normal_handler.handle(line_info)


class EmacsHandler(PrefilterHandler):

    handler_name = Unicode('emacs')
    esc_strings = List([])

    def handle(self, line_info):
        """Handle input lines marked by python-mode."""

        # Currently, nothing is done.  Later more functionality can be added
        # here if needed.

        # The input cache shouldn't be updated
        return line_info.line


#-----------------------------------------------------------------------------
# Defaults
#-----------------------------------------------------------------------------


_default_transformers = [
    AssignSystemTransformer,
    AssignMagicTransformer,
    PyPromptTransformer,
    IPyPromptTransformer,
]

_default_checkers = [
    EmacsChecker,
    ShellEscapeChecker,
    MacroChecker,
    IPyAutocallChecker,
    MultiLineMagicChecker,
    EscCharsChecker,
    AssignmentChecker,
    AutoMagicChecker,
    AliasChecker,
    PythonOpsChecker,
    AutocallChecker
]

_default_handlers = [
    PrefilterHandler,
    AliasHandler,
    ShellEscapeHandler,
    MacroHandler,
    MagicHandler,
    AutoHandler,
    HelpHandler,
    EmacsHandler
]
