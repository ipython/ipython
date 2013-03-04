"""Implementation of magic functions related to History.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib
import os
from io import open as io_open

# Our own packages
from IPython.core.error import StdinNotImplementedError
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import io

#-----------------------------------------------------------------------------
# Magics class implementation
#-----------------------------------------------------------------------------

@magics_class
class HistoryMagics(Magics):

    @skip_doctest
    @line_magic
    def history(self, parameter_s = ''):
        """Print input history (_i<n> variables), with most recent last.

        %history [-o -p -t -n] [-f filename] [range | -g pattern | -l number]

        By default, input history is printed without line numbers so it can be
        directly pasted into an editor. Use -n to show them.

        By default, all input history from the current session is displayed.
        Ranges of history can be indicated using the syntax:
        4      : Line 4, current session
        4-6    : Lines 4-6, current session
        243/1-5: Lines 1-5, session 243
        ~2/7   : Line 7, session 2 before current
        ~8/1-~6/5 : From the first line of 8 sessions ago, to the fifth line
                    of 6 sessions ago.
        Multiple ranges can be entered, separated by spaces

        The same syntax is used by %macro, %save, %edit, %rerun

        Options:

          -n: print line numbers for each input.
          This feature is only available if numbered prompts are in use.

          -o: also print outputs for each input.

          -p: print classic '>>>' python prompts before each input.  This is
           useful for making documentation, and in conjunction with -o, for
           producing doctest-ready output.

          -r: (default) print the 'raw' history, i.e. the actual commands you
           typed.

          -t: print the 'translated' history, as IPython understands it.
          IPython filters your input and converts it all into valid Python
          source before executing it (things like magics or aliases are turned
          into function calls, for example). With this option, you'll see the
          native history instead of the user-entered version: '%cd /' will be
          seen as 'get_ipython().magic("%cd /")' instead of '%cd /'.

          -g: treat the arg as a pattern to grep for in (full) history.
          This includes the saved history (almost all commands ever written).
          Use '%hist -g' to show full saved history (may be very long).

          -l: get the last n lines from all sessions. Specify n as a single
          arg, or the default is the last 10 lines.

          -f FILENAME: instead of printing the output to the screen, redirect
           it to the given file.  The file is always overwritten, though *when
           it can*, IPython asks for confirmation first. In particular, running
           the command 'history -f FILENAME' from the IPython Notebook
           interface will replace FILENAME even if it already exists *without*
           confirmation.

        Examples
        --------
        ::

          In [6]: %hist -n 4-6
          4:a = 12
          5:print a**2
          6:%hist -n 4-6

        """

        opts,args = self.parse_options(parameter_s,'noprtglf:',mode='string')

        # For brevity
        history_manager = self.shell.history_manager

        def _format_lineno(session, line):
            """Helper function to format line numbers properly."""
            if session in (0, history_manager.session_number):
                return str(line)
            return "%s/%s" % (session, line)

        # Check if output to specific file was requested.
        try:
            outfname = opts['f']
        except KeyError:
            outfile = io.stdout  # default
            # We don't want to close stdout at the end!
            close_at_end = False
        else:
            if os.path.exists(outfname):
                try:
                    ans = io.ask_yes_no("File %r exists. Overwrite?" % outfname)
                except StdinNotImplementedError:
                    ans = True
                if not ans:
                    print('Aborting.')
                    return
                print("Overwriting file.")
            outfile = io_open(outfname, 'w', encoding='utf-8')
            close_at_end = True

        print_nums = 'n' in opts
        get_output = 'o' in opts
        pyprompts = 'p' in opts
        # Raw history is the default
        raw = not('t' in opts)

        pattern = None

        if 'g' in opts:         # Glob search
            pattern = "*" + args + "*" if args else "*"
            hist = history_manager.search(pattern, raw=raw, output=get_output)
            print_nums = True
        elif 'l' in opts:       # Get 'tail'
            try:
                n = int(args)
            except (ValueError, IndexError):
                n = 10
            hist = history_manager.get_tail(n, raw=raw, output=get_output)
        else:
            if args:            # Get history by ranges
                hist = history_manager.get_range_by_str(args, raw, get_output)
            else:               # Just get history for the current session
                hist = history_manager.get_range(raw=raw, output=get_output)

        # We could be displaying the entire history, so let's not try to pull
        # it into a list in memory. Anything that needs more space will just
        # misalign.
        width = 4

        for session, lineno, inline in hist:
            # Print user history with tabs expanded to 4 spaces.  The GUI
            # clients use hard tabs for easier usability in auto-indented code,
            # but we want to produce PEP-8 compliant history for safe pasting
            # into an editor.
            if get_output:
                inline, output = inline
            inline = inline.expandtabs(4).rstrip()

            multiline = "\n" in inline
            line_sep = '\n' if multiline else ' '
            if print_nums:
                print(u'%s:%s' % (_format_lineno(session, lineno).rjust(width),
                        line_sep),  file=outfile, end=u'')
            if pyprompts:
                print(u">>> ", end=u"", file=outfile)
                if multiline:
                    inline = "\n... ".join(inline.splitlines()) + "\n..."
            print(inline, file=outfile)
            if get_output and output:
                print(output, file=outfile)

        if close_at_end:
            outfile.close()

    # For a long time we've had %hist as well as %history
    @line_magic
    def hist(self, arg):
        return self.history(arg)

    hist.__doc__ = history.__doc__

    @line_magic
    def rep(self, arg):
        r"""Repeat a command, or get command to input line for editing.

        %recall and %rep are equivalent.

        - %recall (no arguments):

        Place a string version of last computation result (stored in the
        special '_' variable) to the next input prompt. Allows you to create
        elaborate command lines without using copy-paste::

             In[1]: l = ["hei", "vaan"]
             In[2]: "".join(l)
            Out[2]: heivaan
             In[3]: %rep
             In[4]: heivaan_ <== cursor blinking

        %recall 45

        Place history line 45 on the next input prompt. Use %hist to find
        out the number.

        %recall 1-4

        Combine the specified lines into one cell, and place it on the next
        input prompt. See %history for the slice syntax.

        %recall foo+bar

        If foo+bar can be evaluated in the user namespace, the result is
        placed at the next input prompt. Otherwise, the history is searched
        for lines which contain that substring, and the most recent one is
        placed at the next input prompt.
        """
        if not arg:                 # Last output
            self.shell.set_next_input(str(self.shell.user_ns["_"]))
            return
                                    # Get history range
        histlines = self.shell.history_manager.get_range_by_str(arg)
        cmd = "\n".join(x[2] for x in histlines)
        if cmd:
            self.shell.set_next_input(cmd.rstrip())
            return

        try:                        # Variable in user namespace
            cmd = str(eval(arg, self.shell.user_ns))
        except Exception:           # Search for term in history
            histlines = self.shell.history_manager.search("*"+arg+"*")
            for h in reversed([x[2] for x in histlines]):
                if 'rep' in h:
                    continue
                self.shell.set_next_input(h.rstrip())
                return
        else:
            self.shell.set_next_input(cmd.rstrip())
        print("Couldn't evaluate or find in history:", arg)

    @line_magic
    def rerun(self, parameter_s=''):
        """Re-run previous input

        By default, you can specify ranges of input history to be repeated
        (as with %history). With no arguments, it will repeat the last line.

        Options:

          -l <n> : Repeat the last n lines of input, not including the
          current command.

          -g foo : Repeat the most recent line which contains foo
        """
        opts, args = self.parse_options(parameter_s, 'l:g:', mode='string')
        if "l" in opts:         # Last n lines
            n = int(opts['l'])
            hist = self.shell.history_manager.get_tail(n)
        elif "g" in opts:       # Search
            p = "*"+opts['g']+"*"
            hist = list(self.shell.history_manager.search(p))
            for l in reversed(hist):
                if "rerun" not in l[2]:
                    hist = [l]     # The last match which isn't a %rerun
                    break
            else:
                hist = []          # No matches except %rerun
        elif args:              # Specify history ranges
            hist = self.shell.history_manager.get_range_by_str(args)
        else:                   # Last line
            hist = self.shell.history_manager.get_tail(1)
        hist = [x[2] for x in hist]
        if not hist:
            print("No lines in history match specification")
            return
        histlines = "\n".join(hist)
        print("=== Executing: ===")
        print(histlines)
        print("=== Output: ===")
        self.shell.run_cell("\n".join(hist), store_history=False)

    @line_magic
    def recall(self,arg):
        self.rep(arg)

    recall.__doc__ = rep.__doc__

