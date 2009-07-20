""" Install various IPython completers

IPython extension that installs the completers related to external apps.

The actual implementations are in extensions/ipy_completers.py

"""
from IPython.core import ipapi

ip = ipapi.get()

from ipy_completers import *

ip.set_hook('complete_command', apt_completer, re_key = '.*apt-get')
ip.set_hook('complete_command', svn_completer, str_key = 'svn')
ip.set_hook('complete_command', hg_completer, str_key = 'hg')

# the old bzr completer is deprecated, we recommend ipy_bzr
#ip.set_hook('complete_command', bzr_completer, str_key = 'bzr')
