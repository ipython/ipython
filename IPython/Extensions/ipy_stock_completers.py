""" Install various IPython completers

IPython extension that installs most of the implemented
custom completers.

The actual implementations are in Extensions/ipy_completers.py

"""
import IPython.ipapi

ip = IPython.ipapi.get()

from ipy_completers import *

ip.set_hook('complete_command', apt_completers, re_key = '.*apt-get')
ip.set_hook('complete_command', apt_completers, re_key = '.*yum')


ip.set_hook('complete_command', module_completer, str_key = 'import')
ip.set_hook('complete_command', module_completer, str_key = 'from')

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

ip.set_hook('complete_command', hg_completer, str_key = 'hg')

ip.set_hook('complete_command', bzr_completer, str_key = 'bzr')

ip.set_hook('complete_command', runlistpy, str_key = '%run')

ip.set_hook('complete_command', cd_completer, str_key = '%cd')
