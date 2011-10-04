""" Implementations for various useful completers

See extensions/ipy_stock_completers.py on examples of how to enable a completer,
but the basic idea is to do:

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

NOTE: some of the completers that used to be here, the ones used always by
default (loaded before by ipy_stock_completers) have been moved into
core.completerlib, where they will be further cleaned up and maintained.  The
rest of this file would need to be well commented, cleaned up and tested for
inclusion into the core.
"""

import glob,os,shlex,sys
import inspect
from time import time
from zipimport import zipimporter

from IPython.core import ipapi
from IPython.core.error import TryNext
ip = ipapi.get()

def vcs_completer(commands, event):
    """ utility to make writing typical version control app completers easier

    VCS command line apps typically have the format:

    [sudo ]PROGNAME [help] [command] file file...

    """


    cmd_param = event.line.split()
    if event.line.endswith(' '):
        cmd_param.append('')

    if cmd_param[0] == 'sudo':
        cmd_param = cmd_param[1:]

    if len(cmd_param) == 2 or 'help' in cmd_param:
        return commands.split()

    return ip.Completer.file_matches(event.symbol)


svn_commands = """\
add blame praise annotate ann cat checkout co cleanup commit ci copy
cp delete del remove rm diff di export help ? h import info list ls
lock log merge mkdir move mv rename ren propdel pdel pd propedit pedit
pe propget pget pg proplist plist pl propset pset ps resolved revert
status stat st switch sw unlock update
"""

def svn_completer(self,event):
    return vcs_completer(svn_commands, event)


hg_commands = """
add addremove annotate archive backout branch branches bundle cat
clone commit copy diff export grep heads help identify import incoming
init locate log manifest merge outgoing parents paths pull push
qapplied qclone qcommit qdelete qdiff qfold qguard qheader qimport
qinit qnew qnext qpop qprev qpush qrefresh qrename qrestore qsave
qselect qseries qtop qunapplied recover remove rename revert rollback
root serve showconfig status strip tag tags tip unbundle update verify
version
"""

def hg_completer(self,event):
    """ Completer for mercurial commands """

    return vcs_completer(hg_commands, event)



__bzr_commands = None

def bzr_commands():
    global __bzr_commands
    if __bzr_commands is not None:
        return __bzr_commands
    out = os.popen('bzr help commands')
    __bzr_commands = [l.split()[0] for l in out]
    return __bzr_commands

def bzr_completer(self,event):
    """ Completer for bazaar commands """
    cmd_param = event.line.split()
    if event.line.endswith(' '):
        cmd_param.append('')

    if len(cmd_param) > 2:
        cmd = cmd_param[1]
        param = cmd_param[-1]
        output_file = (param == '--output=')
        if cmd == 'help':
            return bzr_commands()
        elif cmd in ['bundle-revisions','conflicts',
                     'deleted','nick','register-branch',
                     'serve','unbind','upgrade','version',
                     'whoami'] and not output_file:
            return []
        else:
            # the rest are probably file names
            return ip.Completer.file_matches(event.symbol)

    return bzr_commands()


def apt_get_packages(prefix):
    out = os.popen('apt-cache pkgnames')
    for p in out:
        if p.startswith(prefix):
            yield p.rstrip()


apt_commands = """\
update upgrade install remove purge source build-dep dist-upgrade
dselect-upgrade clean autoclean check"""

def apt_completer(self, event):
    """ Completer for apt-get (uses apt-cache internally)

    """


    cmd_param = event.line.split()
    if event.line.endswith(' '):
        cmd_param.append('')

    if cmd_param[0] == 'sudo':
        cmd_param = cmd_param[1:]

    if len(cmd_param) == 2 or 'help' in cmd_param:
        return apt_commands.split()

    return list(apt_get_packages(event.symbol))
