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

try:
    import IPython
except Exception,e:
    print "Error importing IPython (%s)" % str(e)
    raise Exception, e

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
    def __init__(self, instance, after):
        ThreadEx.__init__(self)
        self.instance = instance
        self._afterExecute = after

    def run(self):
        '''Thread main loop'''
        try:
            self.instance._doc_text = None
            self.instance._help_text = None
            self.instance._execute()
            # used for uper class to generate event after execution
            self._afterExecute() 
            
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

    def __init__(self, argv=[], user_ns={}, user_global_ns=None,
                 cin=None, cout=None, cerr=None,
                 ask_exit_handler=None):
        '''
        @param argv: Command line options for IPython
        @type argv: list
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
        self._term = None
        self.initIpython0(argv, user_ns, user_global_ns,
                          cin, cout, cerr,
                          ask_exit_handler)
        
        #vars used by _execute
        self._iter_more = 0
        self._history_level = 0
        self._complete_sep =  re.compile('[\s\{\}\[\]\(\)\=]')
        self._prompt = str(self._IP.outputcache.prompt1).strip()

        #thread working vars
        self._line_to_execute = ''

        #vars that will be checked by GUI loop to handle thread states...
        #will be replaced later by PostEvent GUI funtions...
        self._doc_text = None
        self._help_text = None
        self._add_button = None

    def initIpython0(self, argv=[], user_ns={}, user_global_ns=None,
                     cin=None, cout=None, cerr=None,
                     ask_exit_handler=None):
        ''' Initialize an ithon0 instance '''
        
        #first we redefine in/out/error functions of IPython 
        if cin:
            IPython.Shell.Term.cin = cin
        if cout:
            IPython.Shell.Term.cout = cout
        if cerr:
            IPython.Shell.Term.cerr = cerr
        
        # This is to get rid of the blockage that accurs during
        # IPython.Shell.InteractiveShell.user_setup()
        IPython.iplib.raw_input = lambda x: None

        self._term = IPython.genutils.IOTerm(cin=cin, cout=cout, cerr=cerr)

        excepthook = sys.excepthook
        #Hack to save sys.displayhook, because ipython seems to overwrite it...
        self.sys_displayhook_ori = sys.displayhook
        
        self._IP = IPython.Shell.make_IPython(
                                    argv,user_ns=user_ns,
                                    user_global_ns=user_global_ns,
                                    embedded=True,
                                    shell_class=IPython.Shell.InteractiveShell)

        #we restore sys.displayhook
        sys.displayhook = self.sys_displayhook_ori

        #we replace IPython default encoding by wx locale encoding
        loc = locale.getpreferredencoding()
        if loc:
            self._IP.stdin_encoding = loc
        #we replace the ipython default pager by our pager
        self._IP.set_hook('show_in_pager', self._pager)
        
        #we replace the ipython default shell command caller by our shell handler
        self._IP.set_hook('shell_hook', self._shell)
        
        #we replace the ipython default input command caller by our method
        IPython.iplib.raw_input_original = self._raw_input
        #we replace the ipython default exit command by our method
        self._IP.exit = ask_exit_handler
        #we replace the help command
        self._IP.user_ns['help'] = _Helper(self._pager_help)

        #we disable cpase magic... until we found a way to use it properly.
        #import IPython.ipapi
        ip = IPython.ipapi.get()
        def bypassMagic(self, arg):
            print '%this magic is currently disabled.'
        ip.expose_magic('cpaste', bypassMagic)
        
        sys.excepthook = excepthook

    #----------------------- Thread management section ----------------------    
    def doExecute(self, line):
        """
        Tell the thread to process the 'line' command
        """

        self._line_to_execute = line
        #we launch the ipython line execution in a thread to make it interruptible
        #with include it in self namespace to be able to call ce.raise_exc(KeyboardInterrupt)
        self.ce = _CodeExecutor(self, self._afterExecute)
        self.ce.start()
        
    #----------------------- IPython management section ----------------------    
    def getDocText(self):
        """
        Returns the output of the processing that need to be paged (if any)

        @return: The std output string.
        @rtype: string
        """
        return self._doc_text
        
    def getHelpText(self):
        """
        Returns the output of the processing that need to be paged via help pager(if any)

        @return: The std output string.
        @rtype: string
        """
        return self._help_text

    def getBanner(self):
        """
        Returns the IPython banner for useful info on IPython instance

        @return: The banner string.
        @rtype: string
        """
        return self._IP.BANNER
    
    def getPromptCount(self):
        """
        Returns the prompt number.
        Each time a user execute a line in the IPython shell the prompt count is increased

        @return: The prompt number
        @rtype: int
        """
        return self._IP.outputcache.prompt_count

    def getPrompt(self):
        """
        Returns current prompt inside IPython instance
        (Can be In [...]: ot ...:)

        @return: The current prompt.
        @rtype: string
        """
        return self._prompt

    def getIndentation(self):
        """
        Returns the current indentation level
        Usefull to put the caret at the good start position if we want to do autoindentation.

        @return: The indentation level.
        @rtype: int
        """
        return self._IP.indent_current_nsp
        
    def updateNamespace(self, ns_dict):
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

            def _commonPrefix(str1, str2):
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
            common_prefix = reduce(_commonPrefix, possibilities)
            completed = line[:-len(split_line[-1])]+common_prefix
        else:
            completed = line
        return completed, possibilities

    def historyBack(self):
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
            history = self._getHistory()            
        return history

    def historyForward(self):
        '''
        Provides one history command forward.

        @return: The command string.
        @rtype: string
        '''
        history = ''
        #the below while loop is used to suppress empty history lines
        while((history == '' or history == '\n') \
        and self._history_level <= self._getHistoryMaxIndex()):
            if self._history_level < self._getHistoryMaxIndex():
                self._history_level += 1
                history = self._getHistory()
            else:
                if self._history_level == self._getHistoryMaxIndex():
                    history = self._getHistory()
                    self._history_level += 1
                else:
                    history = ''
        return history

    def initHistoryIndex(self):
        '''
        set history to last command entered
        '''
        self._history_level = self._getHistoryMaxIndex()+1

    #----------------------- IPython PRIVATE management section --------------
    def _afterExecute(self):
        '''
        Can be redefined to generate post event after excution is done
        '''
        pass

    #def _askExit(self):
    #    '''
    #    Can be redefined to generate post event to exit the Ipython shell
    #    '''
    #    pass

    def _getHistoryMaxIndex(self):
        '''
        returns the max length of the history buffer

        @return: history length
        @rtype: int
        '''
        return len(self._IP.input_hist_raw)-1
        
    def _getHistory(self):
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
        getHelpText function.
        '''
        if self._help_text == None:
            self._help_text = text
        else:
            self._help_text += text
    
    def _pager(self, IP, text):
        '''
        This function is used as a callback replacment to IPython pager function

        It puts the 'text' value inside the self._doc_text string that can be retrived via
        getDocText function.
        '''
        self._doc_text = text
    
    def _raw_input(self, prompt=''):
        '''
        Custom raw_input() replacement. Get's current line from console buffer.

        @param prompt: Prompt to print. Here for compatability as replacement.
        @type prompt: string

        @return: The current command line text.
        @rtype: string
        '''
        return self._line_to_execute

    def _execute(self):
        '''
        Executes the current line provided by the shell object.
        '''
        orig_stdout = sys.stdout
        sys.stdout = IPython.Shell.Term.cout
                
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
            self._iter_more = self._IP.push(line)
            if (self._IP.SyntaxTB.last_syntax_error and self._IP.rc.autoedit_syntax):
                self._IP.edit_syntax_error()
        if self._iter_more:
            self._prompt = str(self._IP.outputcache.prompt2).strip()
            if self._IP.autoindent:
                self._IP.readline_startup_hook(self._IP.pre_readline)
        else:
            self._prompt = str(self._IP.outputcache.prompt1).strip()
            self._IP.indent_current_nsp = 0 #we set indentation to 0
        sys.stdout = orig_stdout
    
    def _shell(self, ip, cmd):
        '''
        Replacement method to allow shell commands without them blocking.

        @param ip: Ipython instance, same as self._IP
        @type cmd: Ipython instance
        @param cmd: Shell command to execute.
        @type cmd: string
        '''
        stdin, stdout = os.popen4(cmd)
        result = stdout.read().decode('cp437').encode(locale.getpreferredencoding())
        #we use print command because the shell command is called
        #inside IPython instance and thus is redirected to thread cout
        #"\x01\x1b[1;36m\x02" <-- add colour to the text...
        print "\x01\x1b[1;36m\x02"+result
        stdout.close()
        stdin.close()
