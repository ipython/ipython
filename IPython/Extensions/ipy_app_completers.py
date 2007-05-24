""" Install various IPython completers

IPython extension that installs the completers related to external apps.

The actual implementations are in Extensions/ipy_completers.py

"""
import IPython.ipapi

ip = IPython.ipapi.get()

from ipy_completers import *

ip.set_hook('complete_command', apt_completers, re_key = '.*apt-get')
ip.set_hook('complete_command', apt_completers, re_key = '.*yum')

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

ip.set_hook('complete_command', hg_completer, str_key = 'hg')

ip.set_hook('complete_command', bzr_completer, str_key = 'bzr')
