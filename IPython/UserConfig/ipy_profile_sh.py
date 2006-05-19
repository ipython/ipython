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
    
    ip.ex('import os')
    ip.ex("def up(): os.chdir('..')")
        
    # Get pysh-like prompt for all profiles. 
    
    o.prompt_in1= '\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
    o.prompt_in2= '\C_Green|\C_LightGreen\D\C_Green> '
    o.prompt_out= '<\#> '
    
    from IPython import Release

    import sys
    # I like my banner minimal.
    o.banner = "Py %s IPy %s\n" % (sys.version.split('\n')[0],Release.version)
    
    # make 'd' an alias for ls -F
    
    ip.magic('alias d ls -F --color=auto')
    
    # Make available all system commands through "rehashing" immediately. 
    # You can comment these lines out to speed up startup on very slow 
    # machines, and to conserve a bit of memory. Note that pysh profile does this
    # automatically
    ip.IP.default_option('cd','-q')
    

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
    for cmd in syscmds:
        #print "al",cmd
        noext, ext = os.path.splitext(cmd)
        ip.IP.alias_table[noext] = (0,cmd)

main()
