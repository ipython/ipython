"""Shell mode for IPython.

Start ipython in shell mode by invoking "ipython -p sh"

(the old version, "ipython -p pysh" still works but this is the more "modern"
shell mode and is recommended for users who don't care about pysh-mode
compatibility)
"""

from IPython.core import ipapi
from IPython.core.error import TryNext
import os,re,textwrap

# The import below effectively obsoletes your old-style ipythonrc[.ini],
# so consider yourself warned!

import ipy_defaults

def main():
    ip = ipapi.get()
    o = ip.options
    # autocall to "full" mode (smart mode is default, I like full mode)

    o.autocall = 2

    # Jason Orendorff's path class is handy to have in user namespace
    # if you are doing shell-like stuff
    try:
        ip.ex("from IPython.external.path import path" )
    except ImportError:
        pass

    # beefed up %env is handy in shell mode
    import envpersist

    # To see where mycmd resides (in path/aliases), do %which mycmd
    import ipy_which

    # tab completers for hg, svn, ...
    import ipy_app_completers

    # To make executables foo and bar in mybin usable without PATH change, do:
    # %rehashdir c:/mybin
    # %store foo
    # %store bar
    import ipy_rehashdir

    # does not work without subprocess module!
    #import ipy_signals

    ip.ex('import os')
    ip.ex("def up(): os.chdir('..')")
    ip.user_ns['LA'] = LastArgFinder()

    # You can assign to _prompt_title variable
    # to provide some extra information for prompt
    # (e.g. the current mode, host/username...)

    ip.user_ns['_prompt_title'] = ''

    # Nice prompt
    o.prompt_in1= r'\C_Green${_prompt_title}\C_LightBlue[\C_LightCyan\Y2\C_LightBlue]\C_Green|\#> '
    o.prompt_in2= r'\C_Green|\C_LightGreen\D\C_Green> '
    o.prompt_out= '<\#> '

    from IPython.core import release

    import sys
    # Non-chatty banner
    o.banner = "IPython %s   [on Py %s]\n" % (release.version,sys.version.split(None,1)[0])


    ip.default_option('cd','-q')
    ip.default_option('macro', '-r')
    # If you only rarely want to execute the things you %edit...
    #ip.default_option('edit','-x')


    o.prompts_pad_left="1"
    # Remove all blank lines in between prompts, like a normal shell.
    o.separate_in="0"
    o.separate_out="0"
    o.separate_out2="0"

    # now alias all syscommands

    db = ip.db

    syscmds = db.get("syscmdlist",[] )
    if not syscmds:
        print textwrap.dedent("""
        System command list not initialized, probably the first run...
        running %rehashx to refresh the command list. Run %rehashx
        again to refresh command list (after installing new software etc.)
        """)
        ip.magic('rehashx')
        syscmds = db.get("syscmdlist")

    # lowcase aliases on win32 only
    if os.name == 'posix':
        mapper = lambda s:s
    else:
        def mapper(s): return s.lower()

    for cmd in syscmds:
        # print "sys",cmd #dbg
        noext, ext = os.path.splitext(cmd)
        if ext.lower() == '.exe':
            cmd = noext

        key = mapper(cmd)
        if key not in ip.alias_manager.alias_table:
            # Dots will be removed from alias names, since ipython
            # assumes names with dots to be python code

            ip.define_alias(key.replace('.',''), cmd)

    # win32 is crippled w/o cygwin, try to help it a little bit
    if sys.platform == 'win32':
        if 'cygwin' in os.environ['PATH'].lower():
            # use the colors of cygwin ls (recommended)
            ip.define_alias('d', 'ls -F --color=auto')
        else:
            # get icp, imv, imkdir, igrep, irm,...
            ip.load('ipy_fsops')

            # and the next best thing to real 'ls -F'
            ip.define_alias('d','dir /w /og /on')

    ip.set_hook('input_prefilter', slash_prefilter_f)
    extend_shell_behavior(ip)

class LastArgFinder:
    """ Allow $LA to work as "last argument of previous command", like $! in bash

    To call this in normal IPython code, do LA()
    """
    def __call__(self, hist_idx = None):
        ip = ipapi.get()
        if hist_idx is None:
            return str(self)
        return ip.input_hist_raw[hist_idx].strip().split()[-1]
    def __str__(self):
        ip = ipapi.get()
        for cmd in reversed(ip.input_hist_raw):
            parts = cmd.strip().split()
            if len(parts) < 2 or parts[-1] in ['$LA', 'LA()']:
                continue
            return parts[-1]
        return ""

def slash_prefilter_f(self,line):
    """ ./foo, ~/foo and /bin/foo now run foo as system command

    Removes the need for doing !./foo, !~/foo or !/bin/foo
    """
    from IPython.utils import genutils
    if re.match('(?:[.~]|/[a-zA-Z_0-9]+)/', line):
        return "get_ipython().system(" + genutils.make_quoted_expr(line)+")"
    raise TryNext

# XXX You do not need to understand the next function!
# This should probably be moved out of profile

def extend_shell_behavior(ip):

    # Instead of making signature a global variable tie it to IPSHELL.
    # In future if it is required to distinguish between different
    # shells we can assign a signature per shell basis
    ip.__sig__ = 0xa005
    # mark the IPSHELL with this signature
    ip.user_ns['__builtins__'].__dict__['__sig__'] = ip.__sig__

    from IPython.external.Itpl import ItplNS
    from IPython.utils.genutils import shell
    # utility to expand user variables via Itpl
    # xxx do something sensible with depth?
    ip.var_expand = lambda cmd, lvars=None, depth=2: \
        str(ItplNS(cmd, ip.user_ns, get_locals()))

    def get_locals():
        """ Substituting a variable through Itpl deep inside the IPSHELL stack
            requires the knowledge of all the variables in scope upto the last
            IPSHELL frame. This routine simply merges all the local variables
            on the IPSHELL stack without worrying about their scope rules
        """
        import sys
        # note lambda expression constitues a function call
        # hence fno should be incremented by one
        getsig = lambda fno: sys._getframe(fno+1).f_globals \
                             ['__builtins__'].__dict__['__sig__']
        getlvars = lambda fno: sys._getframe(fno+1).f_locals
        # trackback until we enter the IPSHELL
        frame_no = 1
        sig = ip.__sig__
        fsig = ~sig
        while fsig != sig :
            try:
                fsig = getsig(frame_no)
            except (AttributeError, KeyError):
                frame_no += 1
            except ValueError:
                # stack is depleted
                # call did not originate from IPSHELL
                return {}
        first_frame = frame_no
        # walk further back until we exit from IPSHELL or deplete stack
        try:
            while(sig == getsig(frame_no+1)):
                frame_no += 1
        except (AttributeError, KeyError, ValueError):
            pass
        # merge the locals from top down hence overriding
        # any re-definitions of variables, functions etc.
        lvars = {}
        for fno in range(frame_no, first_frame-1, -1):
            lvars.update(getlvars(fno))
        #print '\n'*5, first_frame, frame_no, '\n', lvars, '\n'*5 #dbg
        return lvars

    def _runlines(lines):
        """Run a string of one or more lines of source.

        This method is capable of running a string containing multiple source
        lines, as if they had been entered at the IPython prompt.  Since it
        exposes IPython's processing machinery, the given strings can contain
        magic calls (%magic), special shell access (!cmd), etc."""

        # We must start with a clean buffer, in case this is run from an
        # interactive IPython session (via a magic, for example).
        ip.resetbuffer()
        lines = lines.split('\n')
        more = 0
        command = ''
        for line in lines:
            # skip blank lines so we don't mess up the prompt counter, but do
            # NOT skip even a blank line if we are in a code block (more is
            # true)
            # if command is not empty trim the line
            if command != '' :
                line = line.strip()
            # add the broken line to the command
            if line and line[-1] == '\\' :
                command += line[0:-1] + ' '
                more = True
                continue
            else :
                # add the last (current) line to the command
                command += line
                if command or more:
                    # push to raw history, so hist line numbers stay in sync
                    ip.input_hist_raw.append("# " + command + "\n")

                    more = ip.push_line(ip.prefilter(command,more))
                    command = ''
                    # IPython's runsource returns None if there was an error
                    # compiling the code.  This allows us to stop processing right
                    # away, so the user gets the error message at the right place.
                    if more is None:
                        break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            ip.push_line('\n')

    ip.runlines = _runlines

main()
