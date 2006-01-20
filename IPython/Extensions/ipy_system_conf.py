""" System wide configuration file for IPython.

This will be imported by ipython for all users.

After this ipy_user_conf.py is imported, user specific configuration
should reside there. 

 """

import IPython.ipapi as ip

# add system wide configuration information, import extensions etc. here.
# nothing here is essential 

import sys

if sys.version_info >= (2,4):
    # rehashdir extension requires python 2.4
    import ext_rehashdir