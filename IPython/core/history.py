""" History related magics and functionality """
#-----------------------------------------------------------------------------
#  Copyright (C) 2010 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import fnmatch
import os
import sqlite3

# Our own packages
import IPython.utils.io

from IPython.testing import decorators as testdec
from IPython.utils.io import ask_yes_no
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class HistoryManager(object):
    """A class to organize all history-related functionality in one place.
    """
    # Public interface

    # An instance of the IPython shell we are attached to
    shell = None
    # A list to hold processed history
    input_hist_parsed = None
    # A list to hold raw history (as typed by user)
    input_hist_raw = None
    # A list of directories visited during session
    dir_hist = None
    # A dict of output history, keyed with ints from the shell's execution count
    output_hist = None
    # String with path to the history file
    hist_file = None
    # The SQLite database
    db = None
    # The number of the current session in the history database
    session_number = None
    # Should we log output to the database? (default no)
    db_log_output = False
    # Write to database every x commands (higher values save disk access & power)
    #  Values of 1 or less effectively disable caching. 
    db_cache_size = 0
    # The input and output caches
    db_input_cache = None
    db_output_cache = None
    
    # Private interface
    # Variables used to store the three last inputs from the user.  On each new
    # history update, we populate the user's namespace with these, shifted as
    # necessary.
    _i00, _i, _ii, _iii = '','','',''

    # A set with all forms of the exit command, so that we don't store them in
    # the history (it's annoying to rewind the first entry and land on an exit
    # call).
    _exit_commands = None
    
    def __init__(self, shell, load_history=False):
        """Create a new history manager associated with a shell instance.
        
        Parameters
        ----------
        load_history: bool, optional
            If True, history will be loaded from file, and the session
            offset set, so that the next line entered can be retrieved
            as #1.
        """
        # We need a pointer back to the shell for various tasks.
        self.shell = shell
        
        # List of input with multi-line handling. One blank entry so indexing
        # starts from 1.
        self.input_hist_parsed = [""]
        # This one will hold the 'raw' input history, without any
        # pre-processing.  This will allow users to retrieve the input just as
        # it was exactly typed in by the user, with %hist -r.
        self.input_hist_raw = [""]

        # list of visited directories
        try:
            self.dir_hist = [os.getcwd()]
        except OSError:
            self.dir_hist = []

        # dict of output history
        self.output_hist = {}

        # Now the history file
        if shell.profile:
            histfname = 'history-%s' % shell.profile
        else:
            histfname = 'history'
        self.hist_file = os.path.join(shell.ipython_dir, histfname + '.sqlite')
    
        self._i00, self._i, self._ii, self._iii = '','','',''

        self._exit_commands = set(['Quit', 'quit', 'Exit', 'exit', '%Quit',
                                   '%quit', '%Exit', '%exit'])

        self.init_db()
        
    def init_db(self):
        self.db = sqlite3.connect(self.hist_file)
        self.db.execute("""CREATE TABLE IF NOT EXISTS history 
                (session integer, line integer, source text, source_raw text,
                PRIMARY KEY (session, line))""")
        # Output history is optional, but ensure the table's there so it can be
        # enabled later.
        self.db.execute("""CREATE TABLE IF NOT EXISTS output_history
                        (session integer, line integer, output text,
                        PRIMARY KEY (session, line))""")
        cur = self.db.execute("""SELECT name FROM sqlite_master WHERE
                                type='table' AND name='singletons'""")
        if not cur.fetchone():
            self.db.execute("""CREATE TABLE singletons
                            (name text PRIMARY KEY, value)""")
            self.db.execute("""INSERT INTO singletons VALUES
                            ('session_number', 1)""")
            self.db.commit()
        cur = self.db.execute("""SELECT value FROM singletons WHERE
                              name='session_number'""")
        self.session_number = cur.fetchone()[0]
        
        #Increment by one for next session.
        self.db.execute("""UPDATE singletons SET value=? WHERE
                        name='session_number'""", (self.session_number+1,))
        self.db.commit()
        self.db_input_cache = []
        self.db_output_cache = []
                        
    def get_db_history(self, session, start=1, stop=None, raw=True):
        """Retrieve input history from the database by session.
        
        Parameters
        ----------
        session : int
            Session number to retrieve. If negative, counts back from current
            session (so -1 is previous session).
        start : int
            First line to retrieve.
        stop : int
            Last line to retrieve. If None, retrieve to the end of the session.
        raw : bool
            If True, return raw input
            
        Returns
        -------
        An iterator over the desired lines.
        """
        toget = 'source_raw' if raw else 'source'
        if session < 0:
            session += self.session_number
        
        if stop:
            cur = self.db.execute("SELECT " + toget + """ FROM history WHERE
                            session==? AND line BETWEEN ? and ?""",
                            (session, start, stop))
        else:
            cur = self.db.execute("SELECT " + toget + """ FROM history WHERE
                            session==? AND line>=?""", (session, start))
        return (x[0] for x in cur)
                            
    def tail_db_history(self, n=10, raw=True):
        """Get the last n lines from the history database."""
        toget = 'source_raw' if raw else 'source'
        cur = self.db.execute("SELECT " + toget + """ FROM history ORDER BY
                            session DESC, line DESC LIMIT ?""", (n,))
        return (x[0] for x in reversed(cur.fetchall()))
        
    def globsearch_db(self, pattern="*"):
        """Search the database using unix glob-style matching (wildcards * and
        ?, escape using \).
        
        Returns
        -------
        An iterator over tuples: (session, line_number, command)
        """
        return self.db.execute("""SELECT session, line, source_raw FROM history
                                WHERE source_raw GLOB ?""", (pattern,))
        
    def get_history(self, start=1, stop=None, raw=False, output=True):
        """Get the history list.

        Get the input and output history.

        Parameters
        ----------
        start : int
            From (prompt number in the current session). Negative numbers count
            back from the end.
        stop : int
            To (prompt number in the current session, exclusive). Negative
            numbers count back from the end, and None goes to the end.
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.
        this_session : bool
            If True, indexing is from 1 at the start of this session.
            If False, indexing is from 1 at the start of the whole history.

        Returns
        -------
        If output is True, then return a dict of tuples, keyed by the prompt
        numbers and with values of (input, output). If output is False, then
        a dict, keyed by the prompt number with the values of input.
        """
        if raw:
            input_hist = self.input_hist_raw
        else:
            input_hist = self.input_hist_parsed
        if output:
            output_hist = self.output_hist
            
        n = len(input_hist)
        if start < 0:
            start += n
        if not stop:
            stop = n
        elif stop < 0:
            stop += n
        
        hist = {}
        for i in range(start, stop):
            if output:
                hist[i] = (input_hist[i], output_hist.get(i))
            else:
                hist[i] = input_hist[i]
        return hist

    def store_inputs(self, line_num, source, source_raw=None):
        """Store source and raw input in history and create input cache
        variables _i*.
        
        Parameters
        ----------
        line_num : int
          The prompt number of this input.
        
        source : str
          Python input.

        source_raw : str, optional
          If given, this is the raw input without any IPython transformations
          applied to it.  If not given, ``source`` is used.
        """
        if source_raw is None:
            source_raw = source
            
        # do not store exit/quit commands
        if source_raw.strip() in self._exit_commands:
            return
        
        self.input_hist_parsed.append(source.rstrip())
        self.input_hist_raw.append(source_raw.rstrip())
        
        self.db_input_cache.append((self.session_number, line_num,
                                    source, source_raw))
        # Trigger to flush cache and write to DB.
        if len(self.db_input_cache) >= self.db_cache_size:
            self.writeout_cache()

        # update the auto _i variables
        self._iii = self._ii
        self._ii = self._i
        self._i = self._i00
        self._i00 = source_raw

        # hackish access to user namespace to create _i1,_i2... dynamically
        new_i = '_i%s' % line_num
        to_main = {'_i': self._i,
                   '_ii': self._ii,
                   '_iii': self._iii,
                   new_i : self._i00 }
        self.shell.user_ns.update(to_main)
        
    def store_output(self, line_num, output):
        if not self.db_log_output:
            return
        db_row = (self.session_number, line_num, output)
        if self.db_cache_size > 1:
            self.db_output_cache.append(db_row)
        else:
          with self.db:
            self.db.execute("INSERT INTO output_history VALUES (?,?,?)", db_row)
        
    def writeout_cache(self):
        with self.db:
            self.db.executemany("INSERT INTO history VALUES (?, ?, ?, ?)",
                                self.db_input_cache)
            self.db.executemany("INSERT INTO output_history VALUES (?, ?, ?)",
                                self.db_output_cache)
        self.db_input_cache = []
        self.db_output_cache = []

    def sync_inputs(self):
        """Ensure raw and translated histories have same length."""
        lr = len(self.input_hist_raw)
        lp = len(self.input_hist_parsed)
        if lp < lr:
            self.input_hist_raw[:lr-lp] = []
        elif lr < lp:
            self.input_hist_parsed[:lp-lr] = []

    def reset(self):
        """Clear all histories managed by this object."""
        self.input_hist_parsed[:] = []
        self.input_hist_raw[:] = []
        self.output_hist.clear()
        # The directory history can't be completely empty
        self.dir_hist[:] = [os.getcwd()]

@testdec.skip_doctest
def magic_history(self, parameter_s = ''):
    """Print input history (_i<n> variables), with most recent last.
    
    %history       -> print at most 40 inputs (some may be multi-line)\\
    %history n     -> print at most n inputs\\
    %history n1 n2 -> print inputs between n1 and n2 (n2 not included)\\

    By default, input history is printed without line numbers so it can be
    directly pasted into an editor.

    With -n, each input's number <n> is shown, and is accessible as the
    automatically generated variable _i<n> as well as In[<n>].  Multi-line
    statements are printed starting at a new line for easy copy/paste.

    Options:

      -n: print line numbers for each input.
      This feature is only available if numbered prompts are in use.

      -o: also print outputs for each input.

      -p: print classic '>>>' python prompts before each input.  This is useful
       for making documentation, and in conjunction with -o, for producing
       doctest-ready output.

      -r: (default) print the 'raw' history, i.e. the actual commands you typed.
      
      -t: print the 'translated' history, as IPython understands it.  IPython
      filters your input and converts it all into valid Python source before
      executing it (things like magics or aliases are turned into function
      calls, for example). With this option, you'll see the native history
      instead of the user-entered version: '%cd /' will be seen as
      'get_ipython().magic("%cd /")' instead of '%cd /'.
      
      -g: treat the arg as a pattern to grep for in (full) history.
      This includes the saved history (almost all commands ever written).
      Use '%hist -g' to show full saved history (may be very long).

      -f FILENAME: instead of printing the output to the screen, redirect it to
       the given file.  The file is always overwritten, though IPython asks for
       confirmation first if it already exists.
       
    Examples
    --------
    ::
    
      In [6]: %hist -n 4 6
      4:a = 12
      5:print a**2

    """

    if not self.shell.displayhook.do_full_cache:
        print('This feature is only available if numbered prompts are in use.')
        return
    opts,args = self.parse_options(parameter_s,'gnoptsrf:',mode='list')
    
    # For brevity
    history_manager = self.shell.history_manager

    # Check if output to specific file was requested.
    try:
        outfname = opts['f']
    except KeyError:
        outfile = IPython.utils.io.Term.cout  # default
        # We don't want to close stdout at the end!
        close_at_end = False
    else:
        if os.path.exists(outfname):
            if not ask_yes_no("File %r exists. Overwrite?" % outfname): 
                print('Aborting.')
                return

        outfile = open(outfname,'w')
        close_at_end = True
    
    print_nums = 'n' in opts
    print_outputs = 'o' in opts
    pyprompts = 'p' in opts
    # Raw history is the default
    raw = not('t' in opts)
            
    default_length = 40
    pattern = None
    if 'g' in opts:
        start = 1; stop = None
        parts = parameter_s.split(None, 1)
        if len(parts) == 1:
            parts += '*'
        head, pattern = parts
        pattern = "*" + pattern + "*"
    elif len(args) == 0:
        start = 1; stop = None
    elif len(args) == 1:
        start = -int(args[0]); stop=None
    elif len(args) == 2:
        start = int(args[0]); stop = int(args[1])
    else:
        warn('%hist takes 0, 1 or 2 arguments separated by spaces.')
        print(self.magic_hist.__doc__, file=IPython.utils.io.Term.cout)
        return
        
    hist = history_manager.get_history(start, stop, raw, print_outputs)
    
    width = len(str(max(hist.iterkeys())))
    line_sep = ['','\n']
    
    found = False
    if pattern is not None:
        for session, line, s in history_manager.globsearch_db(pattern):
            print("%d#%d: %s" %(session, line, s.expandtabs(4)), file=outfile)
            found = True
    
    if found:
        print("===", file=outfile)
        print("shadow history ends, fetch by %rep session#line",
              file=outfile)
        print("=== start of normal history ===", file=outfile)
        
    for in_num, inline in sorted(hist.iteritems()):
        # Print user history with tabs expanded to 4 spaces.  The GUI clients
        # use hard tabs for easier usability in auto-indented code, but we want
        # to produce PEP-8 compliant history for safe pasting into an editor.
        if print_outputs:
            inline, output = inline
        inline = inline.expandtabs(4).rstrip()

        if pattern is not None and not fnmatch.fnmatch(inline, pattern):
            continue
            
        multiline = "\n" in inline
        if print_nums:
            print('%s:%s' % (str(in_num).ljust(width), line_sep[multiline]),
                  file=outfile, end='')
        if pyprompts:
            print(">>> ", end="", file=outfile)
            if multiline:
                inline = "\n... ".join(inline.splitlines()) + "\n..."
        print(inline, file=outfile)
        if print_outputs and output:
            print(repr(output), file=outfile)

    if close_at_end:
        outfile.close()

# %hist is an alternative name
magic_hist = magic_history


def rep_f(self, arg):
    r""" Repeat a command, or get command to input line for editing

    - %rep (no arguments):
    
    Place a string version of last computation result (stored in the special '_'
    variable) to the next input prompt. Allows you to create elaborate command
    lines without using copy-paste::
    
        $ l = ["hei", "vaan"]       
        $ "".join(l)        
        ==> heivaan        
        $ %rep        
        $ heivaan_ <== cursor blinking    
    
    %rep 45
    
    Place history line 45 to next input prompt. Use %hist to find out the
    number.
    
    %rep 1-4 6-7 3
    
    Repeat the specified lines immediately. Input slice syntax is the same as
    in %macro and %save.
    
    %rep foo
    
    Place the most recent line that has the substring "foo" to next input.
    (e.g. 'svn ci -m foobar').    
    """
    
    opts,args = self.parse_options(arg,'',mode='list')
    if not args:
        self.set_next_input(str(self.shell.user_ns["_"]))
        return

    if len(args) == 1 and not '-' in args[0]:
        arg = args[0]
        if len(arg) > 1 and arg.startswith('0'):
            # get from shadow hist
            num = int(arg[1:])
            line = self.shell.shadowhist.get(num)
            self.set_next_input(str(line))
            return
        try:
            num = int(args[0])
            self.set_next_input(str(self.shell.input_hist_raw[num]).rstrip())
            return
        except ValueError:
            pass
        
        for h in reversed(self.shell.input_hist_raw):
            if 'rep' in h:
                continue
            if fnmatch.fnmatch(h,'*' + arg + '*'):
                self.set_next_input(str(h).rstrip())
                return
        
    try:
        lines = self.extract_input_slices(args, True)
        print("lines", lines)
        self.run_cell(lines)
    except ValueError:
        print("Not found in recent history:", args)


def init_ipython(ip):
    ip.define_magic("rep",rep_f)        
    ip.define_magic("hist",magic_hist)            
    ip.define_magic("history",magic_history)

    # XXX - ipy_completers are in quarantine, need to be updated to new apis
    #import ipy_completers
    #ipy_completers.quick_completer('%hist' ,'-g -t -r -n')
