""" User configuration file for IPython

This is a more flexible and safe way to configure ipython than *rc files
(ipythonrc, ipythonrc-pysh etc.)

This file is always imported on ipython startup. You can import the
ipython extensions you need here (see IPython/Extensions directory).

Feel free to edit this file to customize your ipython experience.

Note that as such this file does nothing, for backwards compatibility.
To enable this config file, uncomment the call to main() at the end.

Try it out!

"""

# Most of your config files and extensions will probably start with this import

from IPython import ipapi
import os
from IPython import Release

import sys


def main():
    ip = ipapi.get()
    o = ip.options()
    # autocall to "full" mode (smart mode is default, I like full mode)
    
    o.autocall = 1
    
    # Jason Orendorff's path class is handy to have in user namespace
    # if you are doing shell-like stuff
    try:
        ip.ex("from path import path" )
    except ImportError:
        pass
        
    # Get prompt with working dir
    
    o.prompt_in1= '\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
    o.prompt_in2= '\C_Green|\C_LightGreen\D\C_Green> '
    o.prompt_out= '<\#> '
    
    # I like my banner minimal.
    o.banner = "Py %s IPy %s\n" % (sys.version.split('\n')[0],Release.version)
    
    # make 'd' an alias for ls -F
    
    ip.magic('alias d ls -F --color=auto')
    
    # Make available all system commands through "rehashing" immediately. 
    # You can comment these lines out to speed up startup on very slow 
    # machines, and to conserve a bit of memory. Note that pysh profile does this
    # automatically
    
    #if os.name=='posix':
    #    ip.magic('rehash')
    #else:
    #    #slightly slower, but better results esp. with Windows
    #    ip.magic('rehashx')

#main()