""" User configuration file for IPython

This is a more flexible and safe way to configure ipython than *rc files
(ipythonrc, ipythonrc-pysh etc.)

This file is always imported on ipython startup. You should import all the
ipython extensions you need here (see IPython/Extensions directory).

"""

# see IPython.ipapi for configuration tips

import IPython.ipapi as ip


o = ip.options()
# autocall 1 ('smart') is default anyway, this is just an 
# example on how to set an option
o.autocall = 1

if o.profile == 'pysh':
    # Jason Orendorff's path class is handy to have in user namespace
    # if you are doing shell-like stuff
    ip.ex("from IPython.path import path" )
    
# get pysh-like prompt for all profiles. Comment these out for "old style"
# prompts, as determined by *rc files

o.prompt_in1= '\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
o.prompt_in2= '\C_Green|\C_LightGreen\D\C_Green> '
o.prompt_out= '<\#> '

# make 'd' an alias for ls -F

ip.magic('alias d ls -F --color=auto')

# Make available all system commands. Comment out to speed up 
# startup os slow machines and conserve a bit of memory

ip.magic('rehashx')