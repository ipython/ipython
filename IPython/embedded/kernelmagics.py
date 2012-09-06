#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports.
import os

# Local imports
from IPython.core.magic import magics_class, line_magic, Magics
from IPython.core.magics import MacroToEdit, CodeMagics
from IPython.core import page
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import openpy

#-----------------------------------------------------------------------------
# Functions and classes
#-----------------------------------------------------------------------------

@magics_class
class KernelMagics(Magics):
    #------------------------------------------------------------------------
    # Magic overrides
    #------------------------------------------------------------------------
    # Once the base class stops inheriting from magic, this code needs to be
    # moved into a separate machinery as well.  For now, at least isolate here
    # the magics which this class needs to implement differently from the base
    # class, or that are unique to it.

    @line_magic
    def doctest_mode(self, parameter_s=''):
        """Toggle doctest mode on and off.

        This mode is intended to make IPython behave as much as possible like a
        plain Python shell, from the perspective of how its prompts, exceptions
        and output look.  This makes it easy to copy and paste parts of a
        session into doctests.  It does so by:

        - Changing the prompts to the classic ``>>>`` ones.
        - Changing the exception reporting mode to 'Plain'.
        - Disabling pretty-printing of output.

        Note that IPython also supports the pasting of code snippets that have
        leading '>>>' and '...' prompts in them.  This means that you can paste
        doctests from files or docstrings (even if they have leading
        whitespace), and the code will execute correctly.  You can then use
        '%history -t' to see the translated history; this will give you the
        input after removal of all the leading prompts and whitespace, which
        can be pasted back into an editor.

        With these features, you can switch into this mode easily whenever you
        need to do testing and changes to doctests, without having to leave
        your existing IPython session.
        """

        from IPython.utils.ipstruct import Struct

        # Shorthands
        shell = self.shell
        disp_formatter = self.shell.display_formatter
        ptformatter = disp_formatter.formatters['text/plain']
        # dstore is a data store kept in the instance metadata bag to track any
        # changes we make, so we can undo them later.
        dstore = shell.meta.setdefault('doctest_mode', Struct())
        save_dstore = dstore.setdefault

        # save a few values we'll need to recover later
        mode = save_dstore('mode', False)
        save_dstore('rc_pprint', ptformatter.pprint)
        save_dstore('rc_plain_text_only',disp_formatter.plain_text_only)
        save_dstore('xmode', shell.InteractiveTB.mode)

        if mode == False:
            # turn on
            ptformatter.pprint = False
            disp_formatter.plain_text_only = True
            shell.magic('xmode Plain')
        else:
            # turn off
            ptformatter.pprint = dstore.rc_pprint
            disp_formatter.plain_text_only = dstore.rc_plain_text_only
            shell.magic("xmode " + dstore.xmode)

        # Store new mode and inform on console
        dstore.mode = bool(1-int(mode))
        mode_label = ['OFF','ON'][dstore.mode]
        print('Doctest mode is:', mode_label)

        # Send the payload back so that clients can modify their prompt display
        payload = dict(
            source='IPython.zmq.zmqshell.ZMQInteractiveShell.doctest_mode',
            mode=dstore.mode)
        shell.payload_manager.write_payload(payload)
        
    _find_edit_target = CodeMagics._find_edit_target

    @skip_doctest
    @line_magic
    def edit(self, parameter_s='', last_call=['','']):
        """Bring up an editor and execute the resulting code.

        Usage:
          %edit [options] [args]

        %edit runs an external text editor. You will need to set the command for
        this editor via the ``TerminalInteractiveShell.editor`` option in your
        configuration file before it will work.

        This command allows you to conveniently edit multi-line code right in
        your IPython session.

        If called without arguments, %edit opens up an empty editor with a
        temporary file and will execute the contents of this file when you
        close it (don't forget to save it!).


        Options:

        -n <number>: open the editor at a specified line number.  By default,
        the IPython editor hook uses the unix syntax 'editor +N filename', but
        you can configure this by providing your own modified hook if your
        favorite editor supports line-number specifications with a different
        syntax.

        -p: this will call the editor with the same data as the previous time
        it was used, regardless of how long ago (in your current session) it
        was.

        -r: use 'raw' input.  This option only applies to input taken from the
        user's history.  By default, the 'processed' history is used, so that
        magics are loaded in their transformed version to valid Python.  If
        this option is given, the raw input as typed as the command line is
        used instead.  When you exit the editor, it will be executed by
        IPython's own processor.

        -x: do not execute the edited code immediately upon exit. This is
        mainly useful if you are editing programs which need to be called with
        command line arguments, which you can then do using %run.


        Arguments:

        If arguments are given, the following possibilites exist:

        - The arguments are numbers or pairs of colon-separated numbers (like
        1 4:8 9). These are interpreted as lines of previous input to be
        loaded into the editor. The syntax is the same of the %macro command.

        - If the argument doesn't start with a number, it is evaluated as a
        variable and its contents loaded into the editor. You can thus edit
        any string which contains python code (including the result of
        previous edits).

        - If the argument is the name of an object (other than a string),
        IPython will try to locate the file where it was defined and open the
        editor at the point where it is defined. You can use `%edit function`
        to load an editor exactly at the point where 'function' is defined,
        edit it and have the file be executed automatically.

        If the object is a macro (see %macro for details), this opens up your
        specified editor with a temporary file containing the macro's data.
        Upon exit, the macro is reloaded with the contents of the file.

        Note: opening at an exact line is only supported under Unix, and some
        editors (like kedit and gedit up to Gnome 2.8) do not understand the
        '+NUMBER' parameter necessary for this feature. Good editors like
        (X)Emacs, vi, jed, pico and joe all do.

        - If the argument is not found as a variable, IPython will look for a
        file with that name (adding .py if necessary) and load it into the
        editor. It will execute its contents with execfile() when you exit,
        loading any code in the file into your interactive namespace.

        After executing your code, %edit will return as output the code you
        typed in the editor (except when it was an existing file). This way
        you can reload the code in further invocations of %edit as a variable,
        via _<NUMBER> or Out[<NUMBER>], where <NUMBER> is the prompt number of
        the output.

        Note that %edit is also available through the alias %ed.

        This is an example of creating a simple function inside the editor and
        then modifying it. First, start up the editor:

        In [1]: ed
        Editing... done. Executing edited code...
        Out[1]: 'def foo():n    print "foo() was defined in an editing session"n'

        We can then call the function foo():

        In [2]: foo()
        foo() was defined in an editing session

        Now we edit foo.  IPython automatically loads the editor with the
        (temporary) file where foo() was previously defined:

        In [3]: ed foo
        Editing... done. Executing edited code...

        And if we call foo() again we get the modified version:

        In [4]: foo()
        foo() has now been changed!

        Here is an example of how to edit a code snippet successive
        times. First we call the editor:

        In [5]: ed
        Editing... done. Executing edited code...
        hello
        Out[5]: "print 'hello'n"

        Now we call it again with the previous output (stored in _):

        In [6]: ed _
        Editing... done. Executing edited code...
        hello world
        Out[6]: "print 'hello world'n"

        Now we call it with the output #8 (stored in _8, also as Out[8]):

        In [7]: ed _8
        Editing... done. Executing edited code...
        hello again
        Out[7]: "print 'hello again'n"
        """

        opts,args = self.parse_options(parameter_s,'prn:')

        try:
            filename, lineno, _ = CodeMagics._find_edit_target(
                self.shell, args, opts, last_call)
        except MacroToEdit as e:
            # TODO: Implement macro editing over 2 processes.
            print("Macro editing not yet implemented in 2-process model.")
            return

        # Make sure we send to the client an absolute path, in case the working
        # directory of client and kernel don't match
        filename = os.path.abspath(filename)

        payload = {
            'source' : 'IPython.zmq.zmqshell.ZMQInteractiveShell.edit_magic',
            'filename' : filename,
            'line_number' : lineno
        }
        self.shell.payload_manager.write_payload(payload)

    # A few magics that are adapted to the specifics of using pexpect and a
    # remote terminal

    @line_magic
    def clear(self, arg_s):
        """Clear the terminal."""
        if os.name == 'posix':
            self.shell.system("clear")
        else:
            self.shell.system("cls")

    if os.name == 'nt':
        # This is the usual name in windows
        cls = line_magic('cls')(clear)

    # Terminal pagers won't work over pexpect, but we do have our own pager

    @line_magic
    def less(self, arg_s):
        """Show a file through the pager.

        Files ending in .py are syntax-highlighted."""
        if not arg_s:
            raise UsageError('Missing filename.')

        if arg_s.endswith('.py'):
            cont = self.shell.pycolorize(
                openpy.read_py_file(arg_s, skip_encoding_cookie=False))
        else:
            cont = open(arg_s).read()
        page.page(cont)

    more = line_magic('more')(less)

    # Man calls a pager, so we also need to redefine it
    if os.name == 'posix':
        @line_magic
        def man(self, arg_s):
            """Find the man page for the given command and display in pager."""
            page.page(self.shell.getoutput('man %s | col -b' % arg_s,
                                           split=False))
