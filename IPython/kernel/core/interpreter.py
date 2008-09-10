# encoding: utf-8

"""Central interpreter object for an IPython engine.

The interpreter is the object whose job is to process lines of user input and
actually execute them in the user's namespace.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Standard library imports.
from types import FunctionType

import __builtin__
import codeop
import compiler
import sys
import traceback

# Local imports.
from IPython.kernel.core import ultraTB
from IPython.kernel.core.display_trap import DisplayTrap
from IPython.kernel.core.macro import Macro
from IPython.kernel.core.prompts import CachedOutput
from IPython.kernel.core.traceback_trap import TracebackTrap
from IPython.kernel.core.util import Bunch, system_shell
from IPython.external.Itpl import ItplNS

# Global constants
COMPILER_ERROR = 'error'
INCOMPLETE_INPUT = 'incomplete'
COMPLETE_INPUT = 'complete'

##############################################################################
# TEMPORARY!!! fake configuration, while we decide whether to use tconfig or
# not

rc = Bunch()
rc.cache_size = 100
rc.pprint = True
rc.separate_in = '\n'
rc.separate_out = '\n'
rc.separate_out2 = ''
rc.prompt_in1 = r'In [\#]: '
rc.prompt_in2 = r'   .\\D.: '
rc.prompt_out = ''
rc.prompts_pad_left = False

##############################################################################

# Top-level utilities
def default_display_formatters():
    """ Return a list of default display formatters.
    """

    from display_formatter import PPrintDisplayFormatter, ReprDisplayFormatter
    return [PPrintDisplayFormatter(), ReprDisplayFormatter()]

def default_traceback_formatters():
    """ Return a list of default traceback formatters.
    """

    from traceback_formatter import PlainTracebackFormatter
    return [PlainTracebackFormatter()]

# Top-level classes
class NotDefined(object):    pass

class Interpreter(object):
    """ An interpreter object.

    fixme: needs to negotiate available formatters with frontends.

    Important: the interpeter should be built so that it exposes a method
    for each attribute/method of its sub-object. This way it can be
    replaced by a network adapter.
    """

    def __init__(self, user_ns=None, global_ns=None,translator=None,
                 magic=None, display_formatters=None,
                 traceback_formatters=None, output_trap=None, history=None,
                 message_cache=None, filename='<string>', config=None):

        # The local/global namespaces for code execution
        local_ns = user_ns  # compatibility name
        if local_ns is None:
            local_ns = {}
        self.user_ns = local_ns
        # The local namespace
        if global_ns is None:
            global_ns = {}
        self.user_global_ns = global_ns

        # An object that will translate commands into executable Python.
        # The current translator does not work properly so for now we are going
        # without!
        # if translator is None:
        #             from IPython.kernel.core.translator import IPythonTranslator
        #             translator = IPythonTranslator()
        self.translator = translator

        # An object that maintains magic commands.
        if magic is None:
            from IPython.kernel.core.magic import Magic
            magic = Magic(self)
        self.magic = magic

        # A list of formatters for the displayhook.
        if display_formatters is None:
            display_formatters = default_display_formatters()
        self.display_formatters = display_formatters

        # A list of formatters for tracebacks.
        if traceback_formatters is None:
            traceback_formatters = default_traceback_formatters()
        self.traceback_formatters = traceback_formatters

        # The object trapping stdout/stderr.
        if output_trap is None:
            from IPython.kernel.core.output_trap import OutputTrap
            output_trap = OutputTrap()
        self.output_trap = output_trap

        # An object that manages the history.
        if history is None:
            from IPython.kernel.core.history import InterpreterHistory
            history = InterpreterHistory()
        self.history = history
        self.get_history_item = history.get_history_item
        self.get_history_input_cache = history.get_input_cache
        self.get_history_input_after = history.get_input_after

        # An object that caches all of the return messages.
        if message_cache is None:
            from IPython.kernel.core.message_cache import SimpleMessageCache
            message_cache = SimpleMessageCache()
        self.message_cache = message_cache

        # The "filename" of the code that is executed in this interpreter.
        self.filename = filename

        # An object that contains much configuration information.
        if config is None:
            # fixme: Move this constant elsewhere!
            config = Bunch(ESC_MAGIC='%')
        self.config = config

        # Hook managers.
        # fixme: make the display callbacks configurable. In the meantime,
        # enable macros.
        self.display_trap = DisplayTrap(
            formatters=self.display_formatters,
            callbacks=[self._possible_macro],
        )
        self.traceback_trap = TracebackTrap(
            formatters=self.traceback_formatters)

        # This is used temporarily for reformating exceptions in certain
        # cases.  It will go away once the ultraTB stuff is ported
        # to ipython1
        self.tbHandler = ultraTB.FormattedTB(color_scheme='NoColor',
                                                 mode='Context',
                                                 tb_offset=2)

        # An object that can compile commands and remember __future__
        # statements.
        self.command_compiler = codeop.CommandCompiler()

        # A replacement for the raw_input() and input() builtins. Change these
        # attributes later to configure them.
        self.raw_input_builtin = raw_input
        self.input_builtin = input

        # The number of the current cell.
        self.current_cell_number = 1

        # Initialize cache, set in/out prompts and printing system
        self.outputcache = CachedOutput(self,
                                        rc.cache_size,
                                        rc.pprint,
                                        input_sep = rc.separate_in,
                                        output_sep = rc.separate_out,
                                        output_sep2 = rc.separate_out2,
                                        ps1 = rc.prompt_in1,
                                        ps2 = rc.prompt_in2,
                                        ps_out = rc.prompt_out,
                                        pad_left = rc.prompts_pad_left)

        # Need to decide later if this is the right approach, but clients
        # commonly use sys.ps1/2, so it may be best to just set them here
        sys.ps1 = self.outputcache.prompt1.p_str
        sys.ps2 = self.outputcache.prompt2.p_str

        # This is the message dictionary assigned temporarily when running the
        # code.
        self.message = None

        self.setup_namespace()


    #### Public 'Interpreter' interface ########################################

    def formatTraceback(self, et, ev, tb, message=''):
        """Put a formatted version of the traceback into value and reraise.
        
        When exceptions have to be sent over the network, the traceback 
        needs to be put into the value of the exception in a nicely
        formatted way.  The method takes the type, value and tb of an 
        exception and puts a string representation of the tb into the 
        value of the exception and reraises it.
        
        Currently this method uses the ultraTb formatter from IPython trunk.
        Eventually it should simply use the traceback formatters in core
        that are loaded into self.tracback_trap.formatters.
        """
        tbinfo = self.tbHandler.text(et,ev,tb)
        ev._ipython_traceback_text = tbinfo
        return et, ev, tb
        
    def execute(self, commands, raiseException=True):
        """ Execute some IPython commands.

        1. Translate them into Python.
        2. Run them.
        3. Trap stdout/stderr.
        4. Trap sys.displayhook().
        5. Trap exceptions.
        6. Return a message object.

        Parameters
        ----------
        commands : str
            The raw commands that the user typed into the prompt.
        
        Returns
        -------
        message : dict
            The dictionary of responses. See the README.txt in this directory
            for an explanation of the format.
        """

        # Create a message dictionary with all of the information we will be
        # returning to the frontend and other listeners.
        message = self.setup_message()

        # Massage the input and store the raw and translated commands into
        # a dict.
        user_input = dict(raw=commands)
        if self.translator is not None:
            python = self.translator(commands, message)
            if python is None:
                # Something went wrong with the translation. The translator
                # should have added an appropriate entry to the message object.
                return message
        else:
            python = commands
        user_input['translated'] = python
        message['input'] = user_input

        # Set the message object so that any magics executed in the code have
        # access.
        self.message = message

        # Set all of the output/exception traps.
        self.set_traps()
        
        # Actually execute the Python code.
        status = self.execute_python(python)

        # Unset all of the traps.
        self.unset_traps()

        # Unset the message object.
        self.message = None

        # Update the history variables in the namespace.
        # E.g. In, Out, _, __, ___
        if self.history is not None:
            self.history.update_history(self, python)

        # Let all of the traps contribute to the message and then clear their
        # stored information.
        self.output_trap.add_to_message(message)
        self.output_trap.clear()
        self.display_trap.add_to_message(message)
        self.display_trap.clear()
        self.traceback_trap.add_to_message(message)
        # Pull out the type, value and tb of the current exception
        # before clearing it.
        einfo = self.traceback_trap.args
        self.traceback_trap.clear()
        
        # Cache the message.
        self.message_cache.add_message(self.current_cell_number, message)

        # Bump the number.
        self.current_cell_number += 1
        
        # This conditional lets the execute method either raise any
        # exception that has occured in user code OR return the message
        # dict containing the traceback and other useful info.
        if raiseException and einfo:
            raise einfo[0],einfo[1],einfo[2]
        else:
            return message

    def generate_prompt(self, is_continuation):
        """Calculate and return a string with the prompt to display.

        :Parameters:
          is_continuation : bool
            Whether the input line is continuing multiline input or not, so
          that a proper continuation prompt can be computed."""
        
        if is_continuation:
            return str(self.outputcache.prompt2)
        else:
            return str(self.outputcache.prompt1)

    def execute_python(self, python):
        """ Actually run the Python code in the namespace.

        :Parameters:

        python : str
            Pure, exec'able Python code. Special IPython commands should have
            already been translated into pure Python.
        """

        # We use a CommandCompiler instance to compile the code so as to keep
        # track of __future__ imports.
        try:
            commands = self.split_commands(python)
        except (SyntaxError, IndentationError), e:
            # Save the exc_info so compilation related exceptions can be
            # reraised
            self.traceback_trap.args = sys.exc_info()
            self.pack_exception(self.message,e)
            return None

        for cmd in commands:
            try:
                code = self.command_compiler(cmd, self.filename, 'single')
            except (SyntaxError, OverflowError, ValueError), e:
                self.traceback_trap.args = sys.exc_info()
                self.pack_exception(self.message,e)
                # No point in continuing if one block raised
                return None
            else:
                self.execute_block(code)

    def execute_block(self,code):
        """Execute a single block of code in the user namespace.

        Return value: a flag indicating whether the code to be run completed
        successfully:

          - 0: successful execution.
          - 1: an error occurred.
          """
        
        outflag = 1 # start by assuming error, success will reset it
        try:
            exec code in self.user_ns
            outflag = 0
        except SystemExit:
            self.resetbuffer()
            self.traceback_trap.args = sys.exc_info()
        except:
            self.traceback_trap.args = sys.exc_info()

        return outflag

    def execute_macro(self, macro):
        """ Execute the value of a macro.

        Parameters
        ----------
        macro : Macro
        """

        python = macro.value
        if self.translator is not None:
            python = self.translator(python)
        self.execute_python(python)

    def getCommand(self, i=None):
        """Gets the ith message in the message_cache.
        
        This is implemented here for compatibility with the old ipython1 shell
        I am not sure we need this though.  I even seem to remember that we
        were going to get rid of it.
        """
        return self.message_cache.get_message(i)

    def reset(self):
        """Reset the interpreter.
        
        Currently this only resets the users variables in the namespace.
        In the future we might want to also reset the other stateful
        things like that the Interpreter has, like In, Out, etc.
        """
        self.user_ns.clear()
        self.setup_namespace()

    def complete(self,line,text=None, pos=None):
        """Complete the given text.

        :Parameters:

          text : str
            Text fragment to be completed on.  Typically this is
        """
        # fixme: implement
        raise NotImplementedError

    def push(self, ns):
        """ Put value into the namespace with name key.
        
        Parameters
        ----------
        **kwds
        """

        self.user_ns.update(ns)

    def push_function(self, ns):
        # First set the func_globals for all functions to self.user_ns
        new_kwds = {}
        for k, v in ns.iteritems():
            if not isinstance(v, FunctionType):
                raise TypeError("function object expected")
            new_kwds[k] = FunctionType(v.func_code, self.user_ns)
        self.user_ns.update(new_kwds)        

    def pack_exception(self,message,exc):
        message['exception'] = exc.__class__
        message['exception_value'] = \
            traceback.format_exception_only(exc.__class__, exc)

    def feed_block(self, source, filename='<input>', symbol='single'):
        """Compile some source in the interpreter.

        One several things can happen:

        1) The input is incorrect; compile_command() raised an
        exception (SyntaxError or OverflowError).

        2) The input is incomplete, and more input is required;
        compile_command() returned None.  Nothing happens.

        3) The input is complete; compile_command() returned a code
        object.  The code is executed by calling self.runcode() (which
        also handles run-time exceptions, except for SystemExit).

        The return value is:

          - True in case 2

          - False in the other cases, unless an exception is raised, where
          None is returned instead.  This can be used by external callers to
          know whether to continue feeding input or not.

        The return value can be used to decide whether to use sys.ps1 or
        sys.ps2 to prompt the next line."""

        self.message = self.setup_message()

        try:
            code = self.command_compiler(source,filename,symbol)
        except (OverflowError, SyntaxError, IndentationError, ValueError ), e:
            # Case 1
            self.traceback_trap.args = sys.exc_info()
            self.pack_exception(self.message,e)
            return COMPILER_ERROR,False

        if code is None:
            # Case 2: incomplete input.  This means that the input can span
            # multiple lines.  But we still need to decide when to actually
            # stop taking user input.  Later we'll add auto-indentation support
            # somehow.  In the meantime, we'll just stop if there are two lines
            # of pure whitespace at the end.
            last_two = source.rsplit('\n',2)[-2:]
            print 'last two:',last_two  # dbg
            if len(last_two)==2 and all(s.isspace() for s in last_two):
                return COMPLETE_INPUT,False
            else:
                return INCOMPLETE_INPUT, True
        else:
            # Case 3
            return COMPLETE_INPUT, False
        
    def pull(self, keys):
        """ Get an item out of the namespace by key.
        
        Parameters
        ----------
        key : str

        Returns
        -------
        value : object

        Raises
        ------
        TypeError if the key is not a string.
        NameError if the object doesn't exist.
        """

        if isinstance(keys, str):
            result = self.user_ns.get(keys, NotDefined())
            if isinstance(result, NotDefined):
                raise NameError('name %s is not defined' % keys)        
        elif isinstance(keys, (list, tuple)):
            result = []
            for key in keys:
                if not isinstance(key, str):
                    raise TypeError("objects must be keyed by strings.")
                else:
                    r = self.user_ns.get(key, NotDefined())
                    if isinstance(r, NotDefined):
                        raise NameError('name %s is not defined' % key)
                    else:
                        result.append(r)
                    if len(keys)==1:
                        result = result[0]
        else:
            raise TypeError("keys must be a strong or a list/tuple of strings")
        return result

    def pull_function(self, keys):
        return self.pull(keys)

    #### Interactive user API ##################################################

    def ipsystem(self, command):
        """ Execute a command in a system shell while expanding variables in the
        current namespace.

        Parameters
        ----------
        command : str
        """

        # Expand $variables.
        command = self.var_expand(command)

        system_shell(command,
            header='IPython system call: ',
            verbose=self.rc.system_verbose,
        )

    def ipmagic(self, arg_string):
        """ Call a magic function by name.

        ipmagic('name -opt foo bar') is equivalent to typing at the ipython
        prompt:

        In[1]: %name -opt foo bar

        To call a magic without arguments, simply use ipmagic('name').

        This provides a proper Python function to call IPython's magics in any
        valid Python code you can type at the interpreter, including loops and
        compound statements.  It is added by IPython to the Python builtin
        namespace upon initialization.

        Parameters
        ----------
        arg_string : str
            A string containing the name of the magic function to call and any
            additional arguments to be passed to the magic.

        Returns
        -------
        something : object
            The return value of the actual object.
        """

        # Taken from IPython.
        raise NotImplementedError('Not ported yet')

        args = arg_string.split(' ', 1)
        magic_name = args[0]
        magic_name = magic_name.lstrip(self.config.ESC_MAGIC)

        try:
            magic_args = args[1]
        except IndexError:
            magic_args = ''
        fn = getattr(self.magic, 'magic_'+magic_name, None)
        if fn is None:
            self.error("Magic function `%s` not found." % magic_name)
        else:
            magic_args = self.var_expand(magic_args)
            return fn(magic_args)


    #### Private 'Interpreter' interface #######################################

    def setup_message(self):
        """Return a message object.

        This method prepares and returns a message dictionary.  This dict
        contains the various fields that are used to transfer information about
        execution, results, tracebacks, etc, to clients (either in or out of
        process ones).  Because of the need to work with possibly out of
        process clients, this dict MUST contain strictly pickle-safe values.
        """

        return dict(number=self.current_cell_number)
    
    def setup_namespace(self):
        """ Add things to the namespace.
        """

        self.user_ns.setdefault('__name__', '__main__')
        self.user_ns.setdefault('__builtins__', __builtin__)
        self.user_ns['__IP'] = self
        if self.raw_input_builtin is not None:
            self.user_ns['raw_input'] = self.raw_input_builtin
        if self.input_builtin is not None:
            self.user_ns['input'] = self.input_builtin

        builtin_additions = dict(
            ipmagic=self.ipmagic,
        )
        __builtin__.__dict__.update(builtin_additions)

        if self.history is not None:
            self.history.setup_namespace(self.user_ns)

    def set_traps(self):
        """ Set all of the output, display, and traceback traps.
        """

        self.output_trap.set()
        self.display_trap.set()
        self.traceback_trap.set()

    def unset_traps(self):
        """ Unset all of the output, display, and traceback traps.
        """

        self.output_trap.unset()
        self.display_trap.unset()
        self.traceback_trap.unset()

    def split_commands(self, python):
        """ Split multiple lines of code into discrete commands that can be
        executed singly.

        Parameters
        ----------
        python : str
            Pure, exec'able Python code.

        Returns
        -------
        commands : list of str
            Separate commands that can be exec'ed independently.
        """

        # compiler.parse treats trailing spaces after a newline as a
        # SyntaxError.  This is different than codeop.CommandCompiler, which
        # will compile the trailng spaces just fine.  We simply strip any
        # trailing whitespace off.  Passing a string with trailing whitespace
        # to exec will fail however.  There seems to be some inconsistency in
        # how trailing whitespace is handled, but this seems to work.
        python = python.strip()

        # The compiler module does not like unicode. We need to convert
        # it encode it:
        if isinstance(python, unicode):
            # Use the utf-8-sig BOM so the compiler detects this a UTF-8
            # encode string.
            python = '\xef\xbb\xbf' + python.encode('utf-8')

        # The compiler module will parse the code into an abstract syntax tree.
        ast = compiler.parse(python)

        # Uncomment to help debug the ast tree
        # for n in ast.node:
        #     print n.lineno,'->',n
                
        # Each separate command is available by iterating over ast.node. The
        # lineno attribute is the line number (1-indexed) beginning the commands
        # suite.
        # lines ending with ";" yield a Discard Node that doesn't have a lineno
        # attribute.  These nodes can and should be discarded.  But there are
        # other situations that cause Discard nodes that shouldn't be discarded.
        # We might eventually discover other cases where lineno is None and have
        # to put in a more sophisticated test.
        linenos = [x.lineno-1 for x in ast.node if x.lineno is not None]

        # When we finally get the slices, we will need to slice all the way to
        # the end even though we don't have a line number for it. Fortunately,
        # None does the job nicely.
        linenos.append(None)
        lines = python.splitlines()

        # Create a list of atomic commands.
        cmds = []
        for i, j in zip(linenos[:-1], linenos[1:]):
            cmd = lines[i:j]
            if cmd:
                cmds.append('\n'.join(cmd)+'\n')

        return cmds

    def error(self, text):
        """ Pass an error message back to the shell.

        Preconditions
        -------------
        This should only be called when self.message is set. In other words,
        when code is being executed.

        Parameters
        ----------
        text : str
        """

        errors = self.message.get('IPYTHON_ERROR', [])
        errors.append(text)

    def var_expand(self, template):
        """ Expand $variables in the current namespace using Itpl.

        Parameters
        ----------
        template : str
        """

        return str(ItplNS(template, self.user_ns))

    def _possible_macro(self, obj):
        """ If the object is a macro, execute it.
        """

        if isinstance(obj, Macro):
            self.execute_macro(obj)

