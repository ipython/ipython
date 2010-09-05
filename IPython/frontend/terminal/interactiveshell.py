# -*- coding: utf-8 -*-
"""Subclass of InteractiveShell for terminal based frontends."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import __builtin__
import bdb
from contextlib import nested
import os
import re
import sys

from IPython.core.error import TryNext
from IPython.core.usage import interactive_usage, default_banner
from IPython.core.inputlist import InputList
from IPython.core.interactiveshell import InteractiveShell, InteractiveShellABC
from IPython.lib.inputhook import enable_gui
from IPython.lib.pylabtools import pylab_activate
from IPython.utils.terminal import toggle_set_term_title, set_term_title
from IPython.utils.process import abbrev_cwd
from IPython.utils.warn import warn
from IPython.utils.text import num_ini_spaces
from IPython.utils.traitlets import Int, Str, CBool


#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------


def get_default_editor():
    try:
        ed = os.environ['EDITOR']
    except KeyError:
        if os.name == 'posix':
            ed = 'vi'  # the only one guaranteed to be there!
        else:
            ed = 'notepad' # same in Windows!
    return ed


# store the builtin raw_input globally, and use this always, in case user code
# overwrites it (like wx.py.PyShell does)
raw_input_original = raw_input


#-----------------------------------------------------------------------------
# Main class
#-----------------------------------------------------------------------------


class TerminalInteractiveShell(InteractiveShell):

    autoedit_syntax = CBool(False, config=True)
    banner = Str('')
    banner1 = Str(default_banner, config=True)
    banner2 = Str('', config=True)
    confirm_exit = CBool(True, config=True)
    # This display_banner only controls whether or not self.show_banner()
    # is called when mainloop/interact are called.  The default is False
    # because for the terminal based application, the banner behavior
    # is controlled by Global.display_banner, which IPythonApp looks at
    # to determine if *it* should call show_banner() by hand or not.
    display_banner = CBool(False) # This isn't configurable!
    embedded = CBool(False)
    embedded_active = CBool(False)
    editor = Str(get_default_editor(), config=True)
    pager = Str('less', config=True)

    screen_length = Int(0, config=True)
    term_title = CBool(False, config=True)

    def __init__(self, config=None, ipython_dir=None, user_ns=None,
                 user_global_ns=None, custom_exceptions=((),None),
                 usage=None, banner1=None, banner2=None,
                 display_banner=None):

        super(TerminalInteractiveShell, self).__init__(
            config=config, ipython_dir=ipython_dir, user_ns=user_ns,
            user_global_ns=user_global_ns, custom_exceptions=custom_exceptions
        )
        self.init_term_title()
        self.init_usage(usage)
        self.init_banner(banner1, banner2, display_banner)

    #-------------------------------------------------------------------------
    # Things related to the terminal
    #-------------------------------------------------------------------------

    @property
    def usable_screen_length(self):
        if self.screen_length == 0:
            return 0
        else:
            num_lines_bot = self.separate_in.count('\n')+1
            return self.screen_length - num_lines_bot

    def init_term_title(self):
        # Enable or disable the terminal title.
        if self.term_title:
            toggle_set_term_title(True)
            set_term_title('IPython: ' + abbrev_cwd())
        else:
            toggle_set_term_title(False)

    #-------------------------------------------------------------------------
    # Things related to the banner and usage
    #-------------------------------------------------------------------------

    def _banner1_changed(self):
        self.compute_banner()

    def _banner2_changed(self):
        self.compute_banner()

    def _term_title_changed(self, name, new_value):
        self.init_term_title()

    def init_banner(self, banner1, banner2, display_banner):
        if banner1 is not None:
            self.banner1 = banner1
        if banner2 is not None:
            self.banner2 = banner2
        if display_banner is not None:
            self.display_banner = display_banner
        self.compute_banner()

    def show_banner(self, banner=None):
        if banner is None:
            banner = self.banner
        self.write(banner)

    def compute_banner(self):
        self.banner = self.banner1 + '\n'
        if self.profile:
            self.banner += '\nIPython profile: %s\n' % self.profile
        if self.banner2:
            self.banner += '\n' + self.banner2 + '\n'

    def init_usage(self, usage=None):
        if usage is None:
            self.usage = interactive_usage
        else:
            self.usage = usage

    #-------------------------------------------------------------------------
    # Mainloop and code execution logic
    #-------------------------------------------------------------------------

    def mainloop(self, display_banner=None):
        """Start the mainloop.

        If an optional banner argument is given, it will override the
        internally created default banner.
        """
        
        with nested(self.builtin_trap, self.display_trap):

            # if you run stuff with -c <cmd>, raw hist is not updated
            # ensure that it's in sync
            if len(self.input_hist) != len (self.input_hist_raw):
                self.input_hist_raw = InputList(self.input_hist)

            while 1:
                try:
                    self.interact(display_banner=display_banner)
                    #self.interact_with_readline()                
                    # XXX for testing of a readline-decoupled repl loop, call
                    # interact_with_readline above
                    break
                except KeyboardInterrupt:
                    # this should not be necessary, but KeyboardInterrupt
                    # handling seems rather unpredictable...
                    self.write("\nKeyboardInterrupt in interact()\n")

    def interact(self, display_banner=None):
        """Closely emulate the interactive Python console."""

        # batch run -> do not interact        
        if self.exit_now:
            return

        if display_banner is None:
            display_banner = self.display_banner
        if display_banner:
            self.show_banner()

        more = 0
        
        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1
        
        if self.has_readline:
            self.readline_startup_hook(self.pre_readline)
        # exit_now is set by a call to %Exit or %Quit, through the
        # ask_exit callback.
        
        while not self.exit_now:
            self.hooks.pre_prompt_hook()
            if more:
                try:
                    prompt = self.hooks.generate_prompt(True)
                except:
                    self.showtraceback()
                if self.autoindent:
                    self.rl_do_indent = True
                    
            else:
                try:
                    prompt = self.hooks.generate_prompt(False)
                except:
                    self.showtraceback()
            try:
                line = self.raw_input(prompt, more)
                if self.exit_now:
                    # quick exit on sys.std[in|out] close
                    break
                if self.autoindent:
                    self.rl_do_indent = False
                    
            except KeyboardInterrupt:
                #double-guard against keyboardinterrupts during kbdint handling
                try:
                    self.write('\nKeyboardInterrupt\n')
                    self.resetbuffer()
                    # keep cache in sync with the prompt counter:
                    self.displayhook.prompt_count -= 1
    
                    if self.autoindent:
                        self.indent_current_nsp = 0
                    more = 0
                except KeyboardInterrupt:
                    pass
            except EOFError:
                if self.autoindent:
                    self.rl_do_indent = False
                    if self.has_readline:
                        self.readline_startup_hook(None)
                self.write('\n')
                self.exit()
            except bdb.BdbQuit:
                warn('The Python debugger has exited with a BdbQuit exception.\n'
                     'Because of how pdb handles the stack, it is impossible\n'
                     'for IPython to properly format this particular exception.\n'
                     'IPython will resume normal operation.')
            except:
                # exceptions here are VERY RARE, but they can be triggered
                # asynchronously by signal handlers, for example.
                self.showtraceback()
            else:
                more = self.push_line(line)
                if (self.SyntaxTB.last_syntax_error and
                    self.autoedit_syntax):
                    self.edit_syntax_error()

        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

        # Turn off the exit flag, so the mainloop can be restarted if desired
        self.exit_now = False

    def raw_input(self,prompt='',continue_prompt=False):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        Optional inputs:

          - prompt(''): a string to be printed to prompt the user.

          - continue_prompt(False): whether this line is the first one or a
          continuation in a sequence of inputs.
        """
        # growl.notify("raw_input: ", "prompt = %r\ncontinue_prompt = %s" % (prompt, continue_prompt))

        # Code run by the user may have modified the readline completer state.
        # We must ensure that our completer is back in place.

        if self.has_readline:
            self.set_completer()
        
        try:
            line = raw_input_original(prompt).decode(self.stdin_encoding)
        except ValueError:
            warn("\n********\nYou or a %run:ed script called sys.stdin.close()"
                 " or sys.stdout.close()!\nExiting IPython!")
            self.ask_exit()
            return ""

        # Try to be reasonably smart about not re-indenting pasted input more
        # than necessary.  We do this by trimming out the auto-indent initial
        # spaces, if the user's actual input started itself with whitespace.
        #debugx('self.buffer[-1]')

        if self.autoindent:
            if num_ini_spaces(line) > self.indent_current_nsp:
                line = line[self.indent_current_nsp:]
                self.indent_current_nsp = 0
            
        # store the unfiltered input before the user has any chance to modify
        # it.
        if line.strip():
            if continue_prompt:
                self.input_hist_raw[-1] += '%s\n' % line
                if self.has_readline and self.readline_use:
                    try:
                        histlen = self.readline.get_current_history_length()
                        if histlen > 1:
                            newhist = self.input_hist_raw[-1].rstrip()
                            self.readline.remove_history_item(histlen-1)
                            self.readline.replace_history_item(histlen-2,
                                            newhist.encode(self.stdin_encoding))
                    except AttributeError:
                        pass # re{move,place}_history_item are new in 2.4.                
            else:
                self.input_hist_raw.append('%s\n' % line)                
            # only entries starting at first column go to shadow history
            if line.lstrip() == line:
                self.shadowhist.add(line.strip())
        elif not continue_prompt:
            self.input_hist_raw.append('\n')
        try:
            lineout = self.prefilter_manager.prefilter_lines(line,continue_prompt)
        except:
            # blanket except, in case a user-defined prefilter crashes, so it
            # can't take all of ipython with it.
            self.showtraceback()
            return ''
        else:
            return lineout

    # TODO: The following three methods are an early attempt to refactor
    # the main code execution logic. We don't use them, but they may be
    # helpful when we refactor the code execution logic further.
    # def interact_prompt(self):
    #     """ Print the prompt (in read-eval-print loop) 
    # 
    #     Provided for those who want to implement their own read-eval-print loop (e.g. GUIs), not 
    #     used in standard IPython flow.
    #     """
    #     if self.more:
    #         try:
    #             prompt = self.hooks.generate_prompt(True)
    #         except:
    #             self.showtraceback()
    #         if self.autoindent:
    #             self.rl_do_indent = True
    # 
    #     else:
    #         try:
    #             prompt = self.hooks.generate_prompt(False)
    #         except:
    #             self.showtraceback()
    #     self.write(prompt)
    # 
    # def interact_handle_input(self,line):
    #     """ Handle the input line (in read-eval-print loop)
    #     
    #     Provided for those who want to implement their own read-eval-print loop (e.g. GUIs), not 
    #     used in standard IPython flow.        
    #     """
    #     if line.lstrip() == line:
    #         self.shadowhist.add(line.strip())
    #     lineout = self.prefilter_manager.prefilter_lines(line,self.more)
    # 
    #     if line.strip():
    #         if self.more:
    #             self.input_hist_raw[-1] += '%s\n' % line
    #         else:
    #             self.input_hist_raw.append('%s\n' % line)                
    # 
    #     
    #     self.more = self.push_line(lineout)
    #     if (self.SyntaxTB.last_syntax_error and
    #         self.autoedit_syntax):
    #         self.edit_syntax_error()
    # 
    # def interact_with_readline(self):
    #     """ Demo of using interact_handle_input, interact_prompt
    #     
    #     This is the main read-eval-print loop. If you need to implement your own (e.g. for GUI),
    #     it should work like this.
    #     """ 
    #     self.readline_startup_hook(self.pre_readline)
    #     while not self.exit_now:
    #         self.interact_prompt()
    #         if self.more:
    #             self.rl_do_indent = True
    #         else:
    #             self.rl_do_indent = False
    #         line = raw_input_original().decode(self.stdin_encoding)
    #         self.interact_handle_input(line)

    #-------------------------------------------------------------------------
    # Methods to support auto-editing of SyntaxErrors.
    #-------------------------------------------------------------------------

    def edit_syntax_error(self):
        """The bottom half of the syntax error handler called in the main loop.

        Loop until syntax error is fixed or user cancels.
        """

        while self.SyntaxTB.last_syntax_error:
            # copy and clear last_syntax_error
            err = self.SyntaxTB.clear_err_state()
            if not self._should_recompile(err):
                return
            try:
                # may set last_syntax_error again if a SyntaxError is raised
                self.safe_execfile(err.filename,self.user_ns)
            except:
                self.showtraceback()
            else:
                try:
                    f = file(err.filename)
                    try:
                        # This should be inside a display_trap block and I 
                        # think it is.
                        sys.displayhook(f.read())
                    finally:
                        f.close()
                except:
                    self.showtraceback()

    def _should_recompile(self,e):
        """Utility routine for edit_syntax_error"""

        if e.filename in ('<ipython console>','<input>','<string>',
                          '<console>','<BackgroundJob compilation>',
                          None):
                              
            return False
        try:
            if (self.autoedit_syntax and 
                not self.ask_yes_no('Return to editor to correct syntax error? '
                              '[Y/n] ','y')):
                return False
        except EOFError:
            return False

        def int0(x):
            try:
                return int(x)
            except TypeError:
                return 0
        # always pass integer line and offset values to editor hook
        try:
            self.hooks.fix_error_editor(e.filename,
                int0(e.lineno),int0(e.offset),e.msg)
        except TryNext:
            warn('Could not open editor')
            return False
        return True

    #-------------------------------------------------------------------------
    # Things related to GUI support and pylab
    #-------------------------------------------------------------------------

    def enable_pylab(self, gui=None):
        """Activate pylab support at runtime.

        This turns on support for matplotlib, preloads into the interactive
        namespace all of numpy and pylab, and configures IPython to correcdtly
        interact with the GUI event loop.  The GUI backend to be used can be
        optionally selected with the optional :param:`gui` argument.

        Parameters
        ----------
        gui : optional, string

          If given, dictates the choice of matplotlib GUI backend to use
          (should be one of IPython's supported backends, 'tk', 'qt', 'wx' or
          'gtk'), otherwise we use the default chosen by matplotlib (as
          dictated by the matplotlib build-time options plus the user's
          matplotlibrc configuration file).
        """
        # We want to prevent the loading of pylab to pollute the user's
        # namespace as shown by the %who* magics, so we execute the activation
        # code in an empty namespace, and we update *both* user_ns and
        # user_ns_hidden with this information.
        ns = {}
        gui = pylab_activate(ns, gui)
        self.user_ns.update(ns)
        self.user_ns_hidden.update(ns)
        # Now we must activate the gui pylab wants to use, and fix %run to take
        # plot updates into account
        enable_gui(gui)
        self.magic_run = self._pylab_magic_run

    #-------------------------------------------------------------------------
    # Things related to exiting
    #-------------------------------------------------------------------------

    def ask_exit(self):
        """ Ask the shell to exit. Can be overiden and used as a callback. """
        self.exit_now = True

    def exit(self):
        """Handle interactive exit.

        This method calls the ask_exit callback."""
        if self.confirm_exit:
            if self.ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                self.ask_exit()
        else:
            self.ask_exit()


InteractiveShellABC.register(TerminalInteractiveShell)
