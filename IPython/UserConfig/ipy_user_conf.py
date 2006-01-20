""" User configuration file for IPython

This is a more flexible and safe way to configure ipython than *rc files
(ipythonrc, ipythonrc-pysh etc.)

This file is always imported on ipython startup. You should import all the
ipython extensions you need here (see IPython/Extensions directory).

Feel free to edit this file to customize your ipython experience. If 
you wish to only use the old config system, it's perfectly ok to make this file 
empty.

"""

# Most of your config files and extensions will probably start with this import

import IPython.ipapi as ip


o = ip.options()
# autocall 1 ('smart') is default anyway, this is just an 
# example on how to set an option
o.autocall = 1

if o.profile == 'pysh':
    # Jason Orendorff's path class is handy to have in user namespace
    # if you are doing shell-like stuff
    ip.ex("from IPython.path import path" )
    
# Uncomment these lines to get pysh-like prompt for all profiles. 

#o.prompt_in1= '\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
#o.prompt_in2= '\C_Green|\C_LightGreen\D\C_Green> '
#o.prompt_out= '<\#> '

# make 'd' an alias for ls -F

ip.magic('alias d ls -F --color=auto')

# Make available all system commands. You can comment this line out to speed up 
# startup on slow machines, and to conserve a bit of memory

ip.magic('rehashx')