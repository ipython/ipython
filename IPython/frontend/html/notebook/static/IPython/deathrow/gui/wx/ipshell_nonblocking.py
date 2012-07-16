#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
'''
Provides IPython remote instance.

@author: Laurent Dufrechou
laurent.dufrechou _at_ gmail.com
@license: BSD

All rights reserved. This program and the accompanying materials are made
available under the terms of the BSD which accompanies this distribution, and
is available at U{http://www.opensource.org/licenses/bsd-license.php}
'''

__version__ = 0.9
__author__  = "Laurent Dufrechou"
__email__   = "laurent.dufrechou _at_ gmail.com"
__license__ = "BSD"

import re
import sys
import os
import locale
from thread_ex import ThreadEx

from IPython.core import iplib
import IPython.utils.io

##############################################################################
class _Helper(object):
    """Redefine the built-in 'help'.
    This is a wrapper around pydoc.help (with a twist).
    """

    def __init__(self, pager):
        self._pager = pager

    def __repr__(self):
        return "Type help() for interactive help, " \
               "or help(object) for help about object."

    def __call__(self, *args, **kwds):
        class DummyWriter(object):
            '''Dumy class to handle help output'''
            def __init__(self, pager):
                self._pager = pager

            def write(self, data):
                '''hook to fill self._pager'''
                self._pager(data)

        import pydoc
        pydoc.help.output = DummyWriter(self._pager)
        pydoc.help.interact = lambda :1

        return pydoc.help(*args, **kwds)


##############################################################################
class _CodeExecutor(ThreadEx):
    ''' Thread that execute ipython code '''
    def __init__(self, instance):
        ThreadEx.__init__(self)
        self.instance = instance

    def run(self):
        '''Thread main loop'''
        try:
            self.instance._doc_text = None
            self.instance._help_text = None
            self.instance._execute()
            # used for uper class to generate event after execution
            self.instance._after_execute()

        except KeyboardInterrupt:
            pass


##############################################################################
class NonBlockingIPShell(object):
    '''
    Create an IPython instance, running the commands in a separate,
    non-blocking thread.
    This allows embedding in any GUI without blockage.

    Note: The ThreadEx class supports asynchroneous function call
          via raise_exc()
    '''

    def __init__(self, user_ns={}, user_global_ns=None,
                 cin=None, cout=None, cerr=None,
                 ask_exit_handler=None):
        '''
        @param user_ns: User namespace.
        @type user_ns: dictionary
        @param user_global_ns: User global namespace.
        @type user_global_ns: dictionary.
        @param cin: Console standard input.
        @type cin: IO stream
        @param cout: Console standard output.
        @type cout: IO stream
        @param cerr: Console standard error.
        @type cerr: IO stream
        @param exit_handler: Replacement for builtin exit() function
        @type exit_handler: function
        @param time_loop: Define the sleep time between two thread's loop
        @type int
        '''
        #ipython0 initialisation
        self._IP = None
        self.init_ipython0(user_ns, user_global_ns,
                           cin, cout, cerr,
                           ask_exit_handler)

        #vars used by _execute
        self._iter_more = 0
        self._history_level = 0
        self._complete_sep =  re.compile('[\s\{\}\[\]\(\)\=]')
        self._prompt = str(self._IP.outputcache.prompt1).strip()

        #thread working vars
        self._line_to_execute = ''
        self._threading = True

        #vars that will be checked by GUI loop to handle thread states...
        #will be replaced later by PostEvent GUI funtions...
        self._doc_text = None
        self._help_text = None
        self._add_button = None

    def init_ipython0(self, user_ns={}, user_global_ns=None,
                     cin=None, cout=None, cerr=None,
                     ask_exit_handler=None):
        ''' Initialize an ipython0 instance '''

        #first we redefine in/out/error functions of IPython
        #BUG: we've got a limitation form ipython0 there
        #only one instance can be instanciated else tehre will be
        #cin/cout/cerr clash...
        if cin:
            Term.cin = cin
        if cout:
            Term.cout = cout
        if cerr:
            Term.cerr = cerr

        excepthook = sys.excepthook

        #Hack to save sys.displayhook, because ipython seems to overwrite it...
        self.sys_displayhook_ori = sys.displayhook
        ipython0 = iplib.InteractiveShell(
            parent=None, config=None,
            user_ns=user_ns,
            user_global_ns=user_global_ns
        )
        self._IP = ipython0

        #we save ipython0 displayhook and we restore sys.displayhook
        self.displayhook = sys.displayhook
        sys.displayhook = self.sys_displayhook_ori

        #we replace IPython default encoding by wx locale encoding
        loc = locale.getpreferredencoding()
        if loc:
            self._IP.stdin_encoding = loc
        #we replace the ipython default pager by our pager
        self._IP.set_hook('show_in_pager', self._pager)

        #we replace the ipython default shell command caller
        #by our shell handler
        self._IP.set_hook('shell_hook', self._shell)

        #we replace the ipython default input command caller by our method
        iplib.raw_input_original = self._raw_input_original
        #we replace the ipython default exit command by our method
        self._IP.exit = ask_exit_handler
        #we replace the help command
        self._IP.user_ns['help'] = _Helper(self._pager_help)

        #we disable cpaste magic... until we found a way to use it properly.
        def bypass_magic(self, arg):
            print '%this magic is currently disabled.'
        ipython0.define_magic('cpaste', bypass_magic)

        import __builtin__
        __builtin__.raw_input = self._raw_input

        sys.excepthook = excepthook

    #----------------------- Thread management section ----------------------
    def do_execute(self, line):
        """
        Tell the thread to process the 'line' command
        """

        self._line_to_execute = line

        if self._threading:
            #we launch the ipython line execution in a thread to make it
            #interruptible with include it in self namespace to be able
            #to call  ce.raise_exc(KeyboardInterrupt)
            self.ce = _CodeExecutor(self)
            self.ce.start()
        else:
            try:
                self._doc_text = None
                self._help_text = None
                self._execute()
                # used for uper class to generate event after execution
                self._after_execute()

            except KeyboardInterrupt:
                pass

    #----------------------- IPython management section ----------------------
    def get_threading(self):
        """
        Returns threading status, is set to True, then each command sent to
        the interpreter will be executed in a separated thread allowing,
        for example, breaking a long running commands.
        Disallowing it, permits better compatibilty with instance that is embedding
        IPython instance.

        @return: Execution method
        @rtype: bool
        """
        return self._threading

    def set_threading(self, state):
        """
        Sets threading state, if set to True, then each command sent to
        the interpreter will be executed in a separated thread allowing,
        for example, breaking a long running commands.
        Disallowing it, permits better compatibilty with instance that is embedding
        IPython instance.

        @param state: Sets threading state
        @type bool
        """
        self._threading = state

    def get_doc_text(self):
        """
        Returns the output of the processing that need to be paged (if any)

        @return: The std output string.
        @rtype: string
        """
        return self._doc_text

    def get_help_text(self):
        """
        Returns the output of the processing that need to be paged via help pager(if any)

        @return: The std output string.
        @rtype: string
        """
        return self._help_text

    def get_banner(self):
        """
        Returns the IPython banner for useful info on IPython instance

        @return: The banner string.
        @rtype: string
        """
        return self._IP.banner

    def get_prompt_count(self):
        """
        Returns the prompt number.
        Each time a user execute a line in the IPython shell the prompt count is increased

        @return: The prompt number
        @rtype: int
        """
        return self._IP.outputcache.prompt_count

    def get_prompt(self):
        """
        Returns current prompt inside IPython instance
        (Can be In [...]: ot ...:)

        @return: The current prompt.
        @rtype: string
        """
        return self._prompt

    def get_indentation(self):
        """
        Returns the current indentation level
        Usefull to put the caret at the good start position if we want to do autoindentation.

        @return: The indentation level.
        @rtype: int
        """
        return self._IP.indent_current_nsp

    def update_namespace(self, ns_dict):
        '''
        Add the current dictionary to the shell namespace.

        @param ns_dict: A dictionary of symbol-values.
        @type ns_dict: dictionary
        '''
        self._IP.user_ns.update(ns_dict)

    def complete(self, line):
        '''
        Returns an auto completed line and/or posibilities for completion.

        @param line: Given line so far.
        @type line: string

        @return: Line completed as for as possible,
        and possible further completions.
        @rtype: tuple
        '''
        split_line = self._complete_sep.split(line)
        possibilities = self._IP.complete(split_line[-1])
        if possibilities:

            def _common_prefix(str1, str2):
                '''
                Reduction function. returns common prefix of two given strings.

                @param str1: First string.
                @type str1: string
                @param str2: Second string
                @type str2: string

                @return: Common prefix to both strings.
                @rtype: string
                '''
                for i in range(len(str1)):
                    if not str2.startswith(str1[:i+1]):
                        return str1[:i]
                return str1
            common_prefix = reduce(_common_prefix, possibilities)
            completed = line[:-len(split_line[-1])]+common_prefix
        else:
            completed = line
        return completed, possibilities

    def history_back(self):
        '''
        Provides one history command back.

        @return: The command string.
        @rtype: string
        '''
        history = ''
        #the below while loop is used to suppress empty history lines
        while((history == '' or history == '\n') and self._history_level >0):
            if self._history_level >= 1:
                self._history_level -= 1
            history = self._get_history()
        return history

    def history_forward(self):
        '''
        Provides one history command forward.

        @return: The command string.
        @rtype: string
        '''
        history = ''
        #the below while loop is used to suppress empty history lines
        while((history == '' or history == '\n') \
        and self._history_level <= self._get_history_max_index()):
            if self._history_level < self._get_history_max_index():
                self._history_level += 1
                history = self._get_history()
            else:
                if self._history_level == self._get_history_max_index():
                    history = self._get_history()
                    self._history_level += 1
                else:
                    history = ''
        return history

    def init_history_index(self):
        '''
        set history to last command entered
        '''
        self._history_level = self._get_history_max_index()+1

    #----------------------- IPython PRIVATE management section --------------
    def _after_execute(self):
        '''
        Can be redefined to generate post event after excution is done
        '''
        pass

    def _ask_exit(self):
        '''
        Can be redefined to generate post event to exit the Ipython shell
        '''
        pass

    def _get_history_max_index(self):
        '''
        returns the max length of the history buffer

        @return: history length
        @rtype: int
        '''
        return len(self._IP.input_hist_raw)-1

    def _get_history(self):
        '''
        Get's the command string of the current history level.

        @return: Historic command stri
        @rtype: string
        '''
        rv = self._IP.input_hist_raw[self._history_level].strip('\n')
        return rv

    def _pager_help(self, text):
        '''
        This function is used as a callback replacment to IPython help pager function

        It puts the 'text' value inside the self._help_text string that can be retrived via
        get_help_text function.
        '''
        if self._help_text == None:
            self._help_text = text
        else:
            self._help_text += text

    def _pager(self, IP, text):
        '''
        This function is used as a callback replacment to IPython pager function

        It puts the 'text' value inside the self._doc_text string that can be retrived via
        get_doc_text function.
        '''
        self._doc_text = text

    def _raw_input_original(self, prompt=''):
        '''
        Custom raw_input() replacement. Get's current line from console buffer.

        @param prompt: Prompt to print. Here for compatability as replacement.
        @type prompt: string

        @return: The current command line text.
        @rtype: string
        '''
        return self._line_to_execute

    def _raw_input(self, prompt=''):
        """ A replacement from python's raw_input.
        """
        raise NotImplementedError

    def _execute(self):
        '''
        Executes the current line provided by the shell object.
        '''

        orig_stdout = sys.stdout
        sys.stdout = Term.cout
        #self.sys_displayhook_ori = sys.displayhook
        #sys.displayhook = self.displayhook

        try:
            line = self._IP.raw_input(None, self._iter_more)
            if self._IP.autoindent:
                self._IP.readline_startup_hook(None)

        except KeyboardInterrupt:
            self._IP.write('\nKeyboardInterrupt\n')
            self._IP.resetbuffer()
            # keep cache in sync with the prompt counter:
            self._IP.outputcache.prompt_count -= 1

            if self._IP.autoindent:
                self._IP.indent_current_nsp = 0
            self._iter_more = 0
        except:
            self._IP.showtraceback()
        else:
            self._IP.write(str(self._IP.outputcache.prompt_out).strip())
            self._iter_more = self._IP.push_line(line)
            if (self._IP.SyntaxTB.last_syntax_error and \
                                                            self._IP.autoedit_syntax):
                self._IP.edit_syntax_error()
        if self._iter_more:
            self._prompt = str(self._IP.outputcache.prompt2).strip()
            if self._IP.autoindent:
                self._IP.readline_startup_hook(self._IP.pre_readline)
        else:
            self._prompt = str(self._IP.outputcache.prompt1).strip()
            self._IP.indent_current_nsp = 0 #we set indentation to 0

        sys.stdout = orig_stdout
        #sys.displayhook = self.sys_displayhook_ori

    def _shell(self, ip, cmd):
        '''
        Replacement method to allow shell commands without them blocking.

        @param ip: Ipython instance, same as self._IP
        @type cmd: Ipython instance
        @param cmd: Shell command to execute.
        @type cmd: string
        '''
        stdin, stdout = os.popen4(cmd)
        result = stdout.read().decode('cp437').\
                                            encode(locale.getpreferredencoding())
        #we use print command because the shell command is called
        #inside IPython instance and thus is redirected to thread cout
        #"\x01\x1b[1;36m\x02" <-- add colour to the text...
        print "\x01\x1b[1;36m\x02"+result
        stdout.close()
        stdin.close()
