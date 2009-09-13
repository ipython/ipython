#!/usr/bin/env python
# encoding: utf-8
"""
Prefiltering components.

Authors:

* Brian Granger
* Fernando Perez
* Dan Milstein
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

import __builtin__
import codeop
import keyword
import os
import re
import sys

from IPython.core.alias import AliasManager
from IPython.core.autocall import IPyAutocall
from IPython.core.component import Component
from IPython.core.splitinput import split_user_input
from IPython.core.page import page

from IPython.utils.traitlets import List, Int, Any, Str, CBool
from IPython.utils.genutils import make_quoted_expr
from IPython.utils.autoattr import auto_attr

#-----------------------------------------------------------------------------
# Global utilities, errors and constants
#-----------------------------------------------------------------------------


ESC_SHELL  = '!'
ESC_SH_CAP = '!!'
ESC_HELP   = '?'
ESC_MAGIC  = '%'
ESC_QUOTE  = ','
ESC_QUOTE2 = ';'
ESC_PAREN  = '/'


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
            or identifier in ip.internal_ns \
            or identifier in ip.ns_table['builtin'])


#-----------------------------------------------------------------------------
# The LineInfo class used throughout
#-----------------------------------------------------------------------------


class LineInfo(object):
    """A single line of input and associated info.

    Includes the following as properties: 

    line
      The original, raw line
    
    continue_prompt
      Is this line a continuation in a sequence of multiline input?
    
    pre
      The initial esc character or whitespace.
    
    pre_char
      The escape character(s) in pre or the empty string if there isn't one.
      Note that '!!' is a possible value for pre_char.  Otherwise it will
      always be a single character.
    
    pre_whitespace
      The leading whitespace from pre if it exists.  If there is a pre_char,
      this is just ''.
    
    ifun
      The 'function part', which is basically the maximal initial sequence
      of valid python identifiers and the '.' character.  This is what is
      checked for alias and magic transformations, used for auto-calling,
      etc.
    
    the_rest
      Everything else on the line.
    """
    def __init__(self, line, continue_prompt):
        self.line            = line
        self.continue_prompt = continue_prompt
        self.pre, self.ifun, self.the_rest = split_user_input(line)

        self.pre_char       = self.pre.strip()
        if self.pre_char:
            self.pre_whitespace = '' # No whitespace allowd before esc chars
        else: 
            self.pre_whitespace = self.pre

        self._oinfo = None

    def ofind(self, ip):
        """Do a full, attribute-walking lookup of the ifun in the various
        namespaces for the given IPython InteractiveShell instance.

        Return a dict with keys: found,obj,ospace,ismagic

        Note: can cause state changes because of calling getattr, but should
        only be run if autocall is on and if the line hasn't matched any
        other, less dangerous handlers.

        Does cache the results of the call, so can be called multiple times
        without worrying about *further* damaging state.
        """
        if not self._oinfo:
            self._oinfo = ip._ofind(self.ifun)
        return self._oinfo

    def __str__(self):                                                         
        return "Lineinfo [%s|%s|%s]" %(self.pre,self.ifun,self.the_rest) 


#-----------------------------------------------------------------------------
# Main Prefilter manager
#-----------------------------------------------------------------------------


class PrefilterManager(Component):
    """Main prefilter component.

    The IPython prefilter is run on all user input before it is run.  The
    prefilter consumes lines of input and produces transformed lines of 
    input.  The implementation consists of checkers and handlers.  The 
    checkers inspect the input line and select which handler will be used
    to transform the input line.
    """

    multi_line_specials = CBool(True, config=True)

    def __init__(self, parent, config=None):
        super(PrefilterManager, self).__init__(parent, config=config)
        self.init_handlers()
        self.init_checkers()

    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    def init_checkers(self):
        self._checkers = []
        for checker in _default_checkers:
            self._checkers.append(checker(self, config=self.config))

    def init_handlers(self):
        self._handlers = {}
        self._esc_handlers = {}
        for handler in _default_handlers:
            handler(self, config=self.config)

    @property
    def sorted_checkers(self):
        """Return a list of checkers, sorted by priority."""
        return sorted(self._checkers, cmp=lambda x,y: x.priority-y.priority)

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

    def prefilter_line_info(self, line_info):
        """Prefilter a line that has been converted to a LineInfo object."""
        handler = self.find_handler(line_info)
        return handler.handle(line_info)

    def find_handler(self, line_info):
        """Find a handler for the line_info by trying checkers."""
        for checker in self.sorted_checkers:
            handler = checker.check(line_info)
            if handler:
                return handler
        return self.get_handler_by_name('normal')

    def prefilter_line(self, line, continue_prompt):
        """Prefilter a single input line as text."""

        # All handlers *must* return a value, even if it's blank ('').

        # Lines are NOT logged here. Handlers should process the line as
        # needed, update the cache AND log it (so that the input cache array
        # stays synced).

        # growl.notify("_prefilter: ", "line = %s\ncontinue_prompt = %s" % (line, continue_prompt))

        # save the line away in case we crash, so the post-mortem handler can
        # record it        
        self.shell._last_input_line = line

        if not line:
            # Return immediately on purely empty lines, so that if the user
            # previously typed some whitespace that started a continuation
            # prompt, he can break out of that loop with just an empty line.
            # This is how the default python prompt works.

            # Only return if the accumulated input buffer was just whitespace!
            if ''.join(self.shell.buffer).isspace():
                self.shell.buffer[:] = []
            return ''
        
        line_info = LineInfo(line, continue_prompt)
        
        # the input history needs to track even empty lines
        stripped = line.strip()

        normal_handler = self.get_handler_by_name('normal')        
        if not stripped:
            if not continue_prompt:
                self.shell.outputcache.prompt_count -= 1

            return normal_handler.handle(line_info)

        # special handlers are only allowed for single line statements
        if continue_prompt and not self.multi_line_specials:
            return normal_handler.handle(line_info)

        return self.prefilter_line_info(line_info)

    def prefilter_lines(self, lines, continue_prompt):
        """Prefilter multiple input lines of text.

        Covers cases where there are multiple lines in the user entry,
        which is the case when the user goes back to a multiline history
        entry and presses enter.
        """
        # growl.notify("multiline_prefilter: ", "%s\n%s" % (line, continue_prompt))
        out = []
        for line in lines.rstrip('\n').split('\n'):
            out.append(self.prefilter_line(line, continue_prompt))
        # growl.notify("multiline_prefilter return: ", '\n'.join(out))
        return '\n'.join(out)


#-----------------------------------------------------------------------------
# Prefilter checkers
#-----------------------------------------------------------------------------


class PrefilterChecker(Component):
    """Inspect an input line and return a handler for that line."""

    priority = Int(100, config=True)
    shell = Any
    prefilter_manager = Any

    def __init__(self, parent, config=None):
        super(PrefilterChecker, self).__init__(parent, config=config)

    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    @auto_attr
    def prefilter_manager(self):
        return PrefilterManager.get_instances(root=self.root)[0]

    def check(self, line_info):
        """Inspect line_info and return a handler or None."""
        return None


class EmacsChecker(PrefilterChecker):

    priority = Int(100, config=True)

    def check(self, line_info):
        "Emacs ipython-mode tags certain input lines."
        if line_info.line.endswith('# PYTHON-MODE'):
            return self.prefilter_manager.get_handler_by_name('emacs')
        else:
            return None


class ShellEscapeChecker(PrefilterChecker):

    priority = Int(200, config=True)

    def check(self, line_info):
        if line_info.line.lstrip().startswith(ESC_SHELL):
            return self.prefilter_manager.get_handler_by_name('shell')


class IPyAutocallChecker(PrefilterChecker):

    priority = Int(300, config=True)

    def check(self, line_info):
        "Instances of IPyAutocall in user_ns get autocalled immediately"
        obj = self.shell.user_ns.get(line_info.ifun, None)
        if isinstance(obj, IPyAutocall):
            obj.set_ip(self.shell)
            return self.prefilter_manager.get_handler_by_name('auto')
        else:
            return None


class MultiLineMagicChecker(PrefilterChecker):

    priority = Int(400, config=True)

    def check(self, line_info):
        "Allow ! and !! in multi-line statements if multi_line_specials is on"
        # Note that this one of the only places we check the first character of
        # ifun and *not* the pre_char.  Also note that the below test matches
        # both ! and !!.    
        if line_info.continue_prompt \
            and self.prefilter_manager.multi_line_specials:
                if line_info.ifun.startswith(ESC_MAGIC):
                    return self.prefilter_manager.get_handler_by_name('magic')
        else:
            return None


class EscCharsChecker(PrefilterChecker):

    priority = Int(500, config=True)

    def check(self, line_info):
        """Check for escape character and return either a handler to handle it,
        or None if there is no escape char."""
        if line_info.line[-1] == ESC_HELP \
               and line_info.pre_char != ESC_SHELL \
               and line_info.pre_char != ESC_SH_CAP:
            # the ? can be at the end, but *not* for either kind of shell escape,
            # because a ? can be a vaild final char in a shell cmd
            return self.prefilter_manager.get_handler_by_name('help')
        else:
            # This returns None like it should if no handler exists
            return self.prefilter_manager.get_handler_by_esc(line_info.pre_char)


class AssignmentChecker(PrefilterChecker):

    priority = Int(600, config=True)

    def check(self, line_info):
        """Check to see if user is assigning to a var for the first time, in
        which case we want to avoid any sort of automagic / autocall games.
    
        This allows users to assign to either alias or magic names true python
        variables (the magic/alias systems always take second seat to true
        python code).  E.g. ls='hi', or ls,that=1,2"""
        if line_info.the_rest and line_info.the_rest[0] in '=,':
            return self.prefilter_manager.get_handler_by_name('normal')
        else:
            return None


class AutoMagicChecker(PrefilterChecker):

    priority = Int(700, config=True)

    def check(self, line_info):
        """If the ifun is magic, and automagic is on, run it.  Note: normal,
        non-auto magic would already have been triggered via '%' in
        check_esc_chars. This just checks for automagic.  Also, before
        triggering the magic handler, make sure that there is nothing in the
        user namespace which could shadow it."""
        if not self.shell.automagic or not hasattr(self.shell,'magic_'+line_info.ifun):
            return None

        # We have a likely magic method.  Make sure we should actually call it.
        if line_info.continue_prompt and not self.shell.multi_line_specials:
            return None

        head = line_info.ifun.split('.',1)[0]
        if is_shadowed(head, self.shell):
            return None

        return self.prefilter_manager.get_handler_by_name('magic')


class AliasChecker(PrefilterChecker):

    priority = Int(800, config=True)

    @auto_attr
    def alias_manager(self):
        return AliasManager.get_instances(root=self.root)[0]

    def check(self, line_info):
        "Check if the initital identifier on the line is an alias."
        # Note: aliases can not contain '.'
        head = line_info.ifun.split('.',1)[0]
        if line_info.ifun not in self.alias_manager \
               or head not in self.alias_manager \
               or is_shadowed(head, self.shell):
            return None

        return self.prefilter_manager.get_handler_by_name('alias')


class PythonOpsChecker(PrefilterChecker):

    priority = Int(900, config=True)

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

    priority = Int(1000, config=True)

    def check(self, line_info):
        "Check if the initial word/function is callable and autocall is on."
        if not self.shell.autocall:
            return None

        oinfo = line_info.ofind(self.shell) # This can mutate state via getattr
        if not oinfo['found']:
            return None
        
        if callable(oinfo['obj']) \
               and (not re_exclude_auto.match(line_info.the_rest)) \
               and re_fun_name.match(line_info.ifun):
            return self.prefilter_manager.get_handler_by_name('auto')
        else:
            return None


#-----------------------------------------------------------------------------
# Prefilter handlers
#-----------------------------------------------------------------------------


class PrefilterHandler(Component):

    handler_name = Str('normal')
    esc_strings = List([])
    shell = Any
    prefilter_manager = Any

    def __init__(self, parent, config=None):
        super(PrefilterHandler, self).__init__(parent, config=config)
        self.prefilter_manager.register_handler(
            self.handler_name,
            self,
            self.esc_strings
        )

    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

    @auto_attr
    def prefilter_manager(self):
        return PrefilterManager.get_instances(root=self.root)[0]

    def handle(self, line_info):
        """Handle normal input lines. Use as a template for handlers."""

        # With autoindent on, we need some way to exit the input loop, and I
        # don't want to force the user to have to backspace all the way to
        # clear the line.  The rule will be in this case, that either two
        # lines of pure whitespace in a row, or a line of pure whitespace but
        # of a size different to the indent level, will exit the input loop.
        line = line_info.line
        continue_prompt = line_info.continue_prompt

        if (continue_prompt and self.shell.autoindent and line.isspace() and
            (0 < abs(len(line) - self.shell.indent_current_nsp) <= 2 or
             (self.shell.buffer[-1]).isspace() )):
            line = ''

        self.shell.log(line, line, continue_prompt)
        return line


class AliasHandler(PrefilterHandler):

    handler_name = Str('alias')
    esc_strings = List([])

    @auto_attr
    def alias_manager(self):
        return AliasManager.get_instances(root=self.root)[0]

    def handle(self, line_info):
        """Handle alias input lines. """
        transformed = self.alias_manager.expand_aliases(line_info.ifun,line_info.the_rest)
        # pre is needed, because it carries the leading whitespace.  Otherwise
        # aliases won't work in indented sections.
        line_out = '%sget_ipython().system(%s)' % (line_info.pre_whitespace,
                                         make_quoted_expr(transformed))
        
        self.shell.log(line_info.line, line_out, line_info.continue_prompt)
        return line_out


class ShellEscapeHandler(PrefilterHandler):

    handler_name = Str('shell')
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
            line_out = '%sget_ipython().system(%s)' % (line_info.pre_whitespace,
                                             make_quoted_expr(cmd))
        # update cache/log and return
        self.shell.log(line, line_out, line_info.continue_prompt)
        return line_out


class MagicHandler(PrefilterHandler):

    handler_name = Str('magic')
    esc_strings = List([ESC_MAGIC])

    def handle(self, line_info):
        """Execute magic functions."""
        ifun    = line_info.ifun
        the_rest = line_info.the_rest
        cmd = '%sget_ipython().magic(%s)' % (line_info.pre_whitespace,
                                   make_quoted_expr(ifun + " " + the_rest))
        self.shell.log(line_info.line, cmd, line_info.continue_prompt)
        return cmd


class AutoHandler(PrefilterHandler):

    handler_name = Str('auto')
    esc_strings = List([ESC_PAREN, ESC_QUOTE, ESC_QUOTE2])

    def handle(self, line_info):
        """Hande lines which can be auto-executed, quoting if requested."""
        line    = line_info.line
        ifun    = line_info.ifun
        the_rest = line_info.the_rest
        pre     = line_info.pre
        continue_prompt = line_info.continue_prompt
        obj = line_info.ofind(self)['obj']

        #print 'pre <%s> ifun <%s> rest <%s>' % (pre,ifun,the_rest)  # dbg

        # This should only be active for single-line input!
        if continue_prompt:
            self.log(line,line,continue_prompt)
            return line

        force_auto = isinstance(obj, IPyAutocall)
        auto_rewrite = True
        
        if pre == ESC_QUOTE:
            # Auto-quote splitting on whitespace
            newcmd = '%s("%s")' % (ifun,'", "'.join(the_rest.split()) )
        elif pre == ESC_QUOTE2:
            # Auto-quote whole string
            newcmd = '%s("%s")' % (ifun,the_rest)
        elif pre == ESC_PAREN:
            newcmd = '%s(%s)' % (ifun,",".join(the_rest.split()))
        else:
            # Auto-paren.
            # We only apply it to argument-less calls if the autocall
            # parameter is set to 2.  We only need to check that autocall is <
            # 2, since this function isn't called unless it's at least 1.
            if not the_rest and (self.shell.autocall < 2) and not force_auto:
                newcmd = '%s %s' % (ifun,the_rest)
                auto_rewrite = False
            else:
                if not force_auto and the_rest.startswith('['):
                    if hasattr(obj,'__getitem__'):
                        # Don't autocall in this case: item access for an object
                        # which is BOTH callable and implements __getitem__.
                        newcmd = '%s %s' % (ifun,the_rest)
                        auto_rewrite = False
                    else:
                        # if the object doesn't support [] access, go ahead and
                        # autocall
                        newcmd = '%s(%s)' % (ifun.rstrip(),the_rest)
                elif the_rest.endswith(';'):
                    newcmd = '%s(%s);' % (ifun.rstrip(),the_rest[:-1])
                else:
                    newcmd = '%s(%s)' % (ifun.rstrip(), the_rest)

        if auto_rewrite:
            rw = self.shell.outputcache.prompt1.auto_rewrite() + newcmd
            
            try:
                # plain ascii works better w/ pyreadline, on some machines, so
                # we use it and only print uncolored rewrite if we have unicode
                rw = str(rw)
                print >>Term.cout, rw
            except UnicodeEncodeError:
                print "-------------->" + newcmd
            
        # log what is now valid Python, not the actual user input (without the
        # final newline)
        self.shell.log(line,newcmd,continue_prompt)
        return newcmd


class HelpHandler(PrefilterHandler):

    handler_name = Str('help')
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
            self.shell.log(line, '#?'+line, line_info.continue_prompt)
            if line:
                #print 'line:<%r>' % line  # dbg
                self.shell.magic_pinfo(line)
            else:
                page(self.shell.usage, screen_lines=self.shell.usable_screen_length)
            return '' # Empty string is needed here!
        except:
            raise
            # Pass any other exceptions through to the normal handler
            return normal_handler.handle(line_info)
        else:
            raise
            # If the code compiles ok, we should handle it normally
            return normal_handler.handle(line_info)


class EmacsHandler(PrefilterHandler):

    handler_name = Str('emacs')
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


_default_checkers = [
    EmacsChecker,
    ShellEscapeChecker,
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
    MagicHandler,
    AutoHandler,
    HelpHandler,
    EmacsHandler
]

