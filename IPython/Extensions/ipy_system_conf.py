""" System wide configuration file for IPython.

This will be imported by ipython for all users.

After this ipy_user_conf.py is imported, user specific configuration
should reside there. 

 """

import IPython.ipapi as ip

# add system wide configuration information, import extensions etc. here.
# nothing here is essential 

import sys

import ext_rehashdir # %rehashdir magic
import ext_rescapture # var = !ls and var = %magic
