"""Shell mode for IPython.

Start ipython in shell mode by invoking "ipython -p sh"

(the old version, "ipython -p pysh" still works but this is the more "modern" 
shell mode and is recommended for users who don't care about pysh-mode
compatibility)
"""

from IPython import ipapi
import os,textwrap

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
        ip.ex("from path import path" )
    except ImportError:
        pass
    
    # beefed up %env is handy in shell mode
    import envpersist
    import ipy_which
    import ipy_app_completers
    import ipy_rehashdir
    import ipy_signals
    
    
    ip.ex('import os')
    ip.ex("def up(): os.chdir('..')")
        
    # Nice prompt
    
    o.prompt_in1= r'\C_LightBlue[\C_LightCyan\Y2\C_LightBlue]\C_Green|\#> '
    o.prompt_in2= r'\C_Green|\C_LightGreen\D\C_Green> '
    o.prompt_out= '<\#> '
    
    from IPython import Release

    import sys
    # I like my banner minimal.
    o.banner = "IPython %s   [on Py %s]\n" % (Release.version,sys.version.split(None,1)[0])
    
    # make 'd' an alias for ls -F
    
    ip.magic('alias d ls -F --color=auto')
    
    ip.IP.default_option('cd','-q')
    
    # If you only rarely want to execute the things you %edit...
    
    #ip.IP.default_option('edit','-x')
    

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
    
    # locase aliases on win#2 only
    if os.name == 'posix':
        mapper = lambda s:s
    else:
        def mapper(s): return s.lower()
        
    for cmd in syscmds:
        #print "al",cmd
        noext, ext = os.path.splitext(cmd)
        ip.IP.alias_table[mapper(noext)] = (0,cmd)


    extend_shell_behavior(ip)

# XXX You do not need to understand the next function!
# This should probably be moved out of profile

def extend_shell_behavior(ip):

    # Instead of making signature a global variable tie it to IPSHELL.
    # In future if it is required to distinguish between different
    # shells we can assign a signature per shell basis
    ip.IP.__sig__ = 0xa005
    # mark the IPSHELL with this signature
    ip.IP.user_ns['__builtins__'].__dict__['__sig__'] = ip.IP.__sig__

    from IPython.Itpl import ItplNS
    from IPython.genutils import shell
    # utility to expand user variables via Itpl
    # xxx do something sensible with depth?
    ip.IP.var_expand = lambda cmd, lvars=None, depth=2: \
        str(ItplNS(cmd.replace('#','\#'), ip.IP.user_ns, get_locals()))

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
        sig = ip.IP.__sig__
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
        ip.IP.resetbuffer()
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
                    more = ip.IP.push(ip.IP.prefilter(command,more))
                    command = ''
                    # IPython's runsource returns None if there was an error
                    # compiling the code.  This allows us to stop processing right
                    # away, so the user gets the error message at the right place.
                    if more is None:
                        break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            ip.IP.push('\n')

    ip.IP.runlines = _runlines

main()
