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
import json
import os
import sys

# Our own packages
import IPython.utils.io

from IPython.utils.pickleshare import PickleShareDB
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
    # PickleShareDB instance holding the raw data for the shadow history
    shadow_db = None
    # ShadowHist instance with the actual shadow history
    shadow_hist = None
    
    # Private interface
    # Variables used to store the three last inputs from the user.  On each new
    # history update, we populate the user's namespace with these, shifted as
    # necessary.
    _i00, _i, _ii, _iii = '','','',''

    # A set with all forms of the exit command, so that we don't store them in
    # the history (it's annoying to rewind the first entry and land on an exit
    # call).
    _exit_commands = None
    
    def __init__(self, shell):
        """Create a new history manager associated with a shell instance.
        """
        # We need a pointer back to the shell for various tasks.
        self.shell = shell
        
        # List of input with multi-line handling.
        self.input_hist_parsed = []
        # This one will hold the 'raw' input history, without any
        # pre-processing.  This will allow users to retrieve the input just as
        # it was exactly typed in by the user, with %hist -r.
        self.input_hist_raw = []

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
        self.hist_file = os.path.join(shell.ipython_dir, histfname + '.json')

        # Objects related to shadow history management
        self._init_shadow_hist()
    
        self._i00, self._i, self._ii, self._iii = '','','',''

        self._exit_commands = set(['Quit', 'quit', 'Exit', 'exit', '%Quit',
                                   '%quit', '%Exit', '%exit'])

        # Object is fully initialized, we can now call methods on it.
        
        # Fill the history zero entry, user counter starts at 1
        self.store_inputs('\n', '\n')

    def _init_shadow_hist(self):
        try:
            self.shadow_db = PickleShareDB(os.path.join(
                                           self.shell.ipython_dir, 'db'))
        except UnicodeDecodeError:
            print("Your ipython_dir can't be decoded to unicode!")
            print("Please set HOME environment variable to something that")
            print(r"only has ASCII characters, e.g. c:\home")
            print("Now it is", self.ipython_dir)
            sys.exit()
        self.shadow_hist = ShadowHist(self.shadow_db, self.shell)
        
    def populate_readline_history(self):
        """Populate the readline history from the raw history.

        We only store one copy of the raw history, which is persisted to a json
        file on disk.  The readline history is repopulated from the contents of
        this file."""

        try:
            self.shell.readline.clear_history()
        except AttributeError:
            pass
        else:
            for h in self.input_hist_raw:
                if not h.isspace():
                    for line in h.splitlines():
                        self.shell.readline.add_history(line)

    def save_history(self):
        """Save input history to a file (via readline library)."""
        hist = dict(raw=self.input_hist_raw, #[-self.shell.history_length:],
                    parsed=self.input_hist_parsed) #[-self.shell.history_length:])
        with open(self.hist_file,'wt') as hfile:
            json.dump(hist, hfile,
                      sort_keys=True, indent=4)
        
    def reload_history(self):
        """Reload the input history from disk file."""

        with open(self.hist_file,'rt') as hfile:
            hist = json.load(hfile)
            self.input_hist_parsed[:] = hist['parsed']
            self.input_hist_raw[:] = hist['raw']
            if self.shell.has_readline:
                self.populate_readline_history()
        
    def get_history(self, index=None, raw=False, output=True):
        """Get the history list.

        Get the input and output history.

        Parameters
        ----------
        index : n or (n1, n2) or None
            If n, then the last entries. If a tuple, then all in
            range(n1, n2). If None, then all entries. Raises IndexError if
            the format of index is incorrect.
        raw : bool
            If True, return the raw input.
        output : bool
            If True, then return the output as well.

        Returns
        -------
        If output is True, then return a dict of tuples, keyed by the prompt
        numbers and with values of (input, output). If output is False, then
        a dict, keyed by the prompt number with the values of input. Raises
        IndexError if no history is found.
        """
        if raw:
            input_hist = self.input_hist_raw
        else:
            input_hist = self.input_hist_parsed
        if output:
            output_hist = self.output_hist
        n = len(input_hist)
        if index is None:
            start=0; stop=n
        elif isinstance(index, int):
            start=n-index; stop=n
        elif isinstance(index, tuple) and len(index) == 2:
            start=index[0]; stop=index[1]
        else:
            raise IndexError('Not a valid index for the input history: %r'
                             % index)
        hist = {}
        for i in range(start, stop):
            if output:
                hist[i] = (input_hist[i], output_hist.get(i))
            else:
                hist[i] = input_hist[i]
        if not hist:
            raise IndexError('No history for range of indices: %r' % index)
        return hist

    def store_inputs(self, source, source_raw=None):
        """Store source and raw input in history and create input cache
        variables _i*.
        
        Parameters
        ----------
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
        self.shadow_hist.add(source)

        # update the auto _i variables
        self._iii = self._ii
        self._ii = self._i
        self._i = self._i00
        self._i00 = source_raw

        # hackish access to user namespace to create _i1,_i2... dynamically
        new_i = '_i%s' % self.shell.execution_count
        to_main = {'_i': self._i,
                   '_ii': self._ii,
                   '_iii': self._iii,
                   new_i : self._i00 }
        self.shell.user_ns.update(to_main)

    def sync_inputs(self):
        """Ensure raw and translated histories have same length."""
        if len(self.input_hist_parsed) != len (self.input_hist_raw):
            self.input_hist_raw[:] = self.input_hist_parsed

    def reset(self):
        """Clear all histories managed by this object."""
        self.input_hist_parsed[:] = []
        self.input_hist_raw[:] = []
        self.output_hist.clear()
        # The directory history can't be completely empty
        self.dir_hist[:] = [os.getcwd()]


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
      This includes the "shadow history" (almost all commands ever written).
      Use '%hist -g' to show full shadow history (may be very long).
      In shadow history, every index nuwber starts with 0.

      -f FILENAME: instead of printing the output to the screen, redirect it to
       the given file.  The file is always overwritten, though IPython asks for
       confirmation first if it already exists.
    """

    if not self.shell.displayhook.do_full_cache:
        print('This feature is only available if numbered prompts are in use.')
        return
    opts,args = self.parse_options(parameter_s,'gnoptsrf:',mode='list')

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

    if 't' in opts:
        input_hist = self.shell.history_manager.input_hist_parsed
    elif 'r' in opts:
        input_hist = self.shell.history_manager.input_hist_raw
    else:
        # Raw history is the default
        input_hist = self.shell.history_manager.input_hist_raw
            
    default_length = 40
    pattern = None
    if 'g' in opts:
        init = 1
        final = len(input_hist)
        parts = parameter_s.split(None, 1)
        if len(parts) == 1:
            parts += '*'
        head, pattern = parts
        pattern = "*" + pattern + "*"
    elif len(args) == 0:
        final = len(input_hist)-1
        init = max(1,final-default_length)
    elif len(args) == 1:
        final = len(input_hist)
        init = max(1, final-int(args[0]))
    elif len(args) == 2:
        init, final = map(int, args)
    else:
        warn('%hist takes 0, 1 or 2 arguments separated by spaces.')
        print(self.magic_hist.__doc__, file=IPython.utils.io.Term.cout)
        return
    
    width = len(str(final))
    line_sep = ['','\n']
    print_nums = 'n' in opts
    print_outputs = 'o' in opts
    pyprompts = 'p' in opts
    
    found = False
    if pattern is not None:
        sh = self.shell.history_manager.shadowhist.all()
        for idx, s in sh:
            if fnmatch.fnmatch(s, pattern):
                print("0%d: %s" %(idx, s.expandtabs(4)), file=outfile)
                found = True
    
    if found:
        print("===", file=outfile)
        print("shadow history ends, fetch by %rep <number> (must start with 0)",
              file=outfile)
        print("=== start of normal history ===", file=outfile)
        
    for in_num in range(init, final):
        # Print user history with tabs expanded to 4 spaces.  The GUI clients
        # use hard tabs for easier usability in auto-indented code, but we want
        # to produce PEP-8 compliant history for safe pasting into an editor.
        inline = input_hist[in_num].expandtabs(4).rstrip()+'\n'

        if pattern is not None and not fnmatch.fnmatch(inline, pattern):
            continue
            
        multiline = int(inline.count('\n') > 1)
        if print_nums:
            print('%s:%s' % (str(in_num).ljust(width), line_sep[multiline]),
                  file=outfile)
        if pyprompts:
            print('>>>', file=outfile)
            if multiline:
                lines = inline.splitlines()
                print('\n... '.join(lines), file=outfile)
                print('... ', file=outfile)
            else:
                print(inline, end='', file=outfile)
        else:
            print(inline, end='', file=outfile)
        if print_outputs:
            output = self.shell.history_manager.output_hist.get(in_num)
            if output is not None:
                print(repr(output), file=outfile)

    if close_at_end:
        outfile.close()


def magic_hist(self, parameter_s=''):
    """Alternate name for %history."""
    return self.magic_history(parameter_s)


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
        

_sentinel = object()

class ShadowHist(object):
    def __init__(self, db, shell):
        # cmd => idx mapping
        self.curidx = 0
        self.db = db
        self.disabled = False
        self.shell = shell
    
    def inc_idx(self):
        idx = self.db.get('shadowhist_idx', 1)
        self.db['shadowhist_idx'] = idx + 1
        return idx
        
    def add(self, ent):
        if self.disabled:
            return
        try:
            old = self.db.hget('shadowhist', ent, _sentinel)
            if old is not _sentinel:
                return
            newidx = self.inc_idx()
            #print("new", newidx) # dbg
            self.db.hset('shadowhist',ent, newidx)
        except:
            self.shell.showtraceback()
            print("WARNING: disabling shadow history")
            self.disabled = True
    
    def all(self):
        d = self.db.hdict('shadowhist')
        items = [(i,s) for (s,i) in d.iteritems()]
        items.sort()
        return items

    def get(self, idx):
        all = self.all()
        
        for k, v in all:
            if k == idx:
                return v


def init_ipython(ip):
    ip.define_magic("rep",rep_f)        
    ip.define_magic("hist",magic_hist)            
    ip.define_magic("history",magic_history)

    # XXX - ipy_completers are in quarantine, need to be updated to new apis
    #import ipy_completers
    #ipy_completers.quick_completer('%hist' ,'-g -t -r -n')
