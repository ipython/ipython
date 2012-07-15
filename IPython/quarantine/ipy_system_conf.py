""" System wide configuration file for IPython.

This will be imported by ipython for all users.

After this ipy_user_conf.py is imported, user specific configuration
should reside there.

 """

from IPython.core import ipapi
ip = ipapi.get()

# add system wide configuration information, import extensions etc. here.
# nothing here is essential

import sys

import ext_rescapture # var = !ls and var = %magic
import pspersistence # %store magic
import clearcmd # %clear

import ipy_stock_completers

ip.load('IPython.core.history')
