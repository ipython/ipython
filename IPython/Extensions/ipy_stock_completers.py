""" Tab completion support for a couple of linux package managers 

This is also an example of how to write custom completer plugins
or hooks.

Practical use:

[ipython]|1> import ipy_linux_package_managers
[ipython]|2> apt-get u<<< press tab here >>>
update  upgrade
[ipython]|2> apt-get up

"""
import IPython.ipapi
import glob,os,shlex,sys

ip = IPython.ipapi.get()

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
    
    return ip.IP.Completer.file_matches(event.symbol)
        
    

def apt_completers(self, event):
    """ This should return a list of strings with possible completions.
    
    Note that all the included strings that don't start with event.symbol
    are removed, in order to not confuse readline.
    
    """
    # print event # dbg
    
    # commands are only suggested for the 'command' part of package manager
    # invocation
        
    cmd = (event.line + "<placeholder>").rsplit(None,1)[0]
    # print cmd
    if cmd.endswith('apt-get') or cmd.endswith('yum'):
        return ['update', 'upgrade', 'install', 'remove']
    
    # later on, add dpkg -l / whatever to get list of possible 
    # packages, add switches etc. for the rest of command line
    # filling
    
    raise IPython.ipapi.TryNext 


# re_key specifies the regexp that triggers the specified completer

ip.set_hook('complete_command', apt_completers, re_key = '.*apt-get')
ip.set_hook('complete_command', apt_completers, re_key = '.*yum')

pkg_cache = None

def module_completer(self,event):    
    """ Give completions after user has typed 'import' """
    
    # only a local version for py 2.4, pkgutil has no walk_packages() there
    if sys.version_info < (2,5):
        for el in [f[:-3] for f in glob.glob("*.py")]:
            yield el
        return

    global pkg_cache
    import pkgutil,imp,time
    #current = 
    if pkg_cache is None:
        print "\n\n[Standby while scanning modules, this can take a while]\n\n"
        pkg_cache = list(pkgutil.walk_packages())
    
    already = set()
    for ld, name, ispkg in pkg_cache:
        if name.count('.') < event.symbol.count('.') + 1:
            if name not in already:
                already.add(name)
                yield name + (ispkg and '.' or '')
    return

ip.set_hook('complete_command', module_completer, str_key = 'import')
ip.set_hook('complete_command', module_completer, str_key = 'from')

svn_commands = """\
add blame praise annotate ann cat checkout co cleanup commit ci copy
cp delete del remove rm diff di export help ? h import info list ls
lock log merge mkdir move mv rename ren propdel pdel pd propedit pedit
pe propget pget pg proplist plist pl propset pset ps resolved revert
status stat st switch sw unlock update
"""

def svn_completer(self,event):
    return vcs_completer(svn_commands, event)

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

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

ip.set_hook('complete_command', hg_completer, str_key = 'hg')


bzr_commands = """
add annotate bind branch break-lock bundle-revisions cat check
checkout commit conflicts deleted diff export gannotate gbranch
gcommit gdiff help ignore ignored info init init-repository inventory
log merge missing mkdir mv nick pull push reconcile register-branch
remerge remove renames resolve revert revno root serve sign-my-commits
status testament unbind uncommit unknowns update upgrade version
version-info visualise whoami
"""

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
            return bzr_commands.split()
        elif cmd in ['bundle-revisions','conflicts',
                     'deleted','nick','register-branch',
                     'serve','unbind','upgrade','version',
                     'whoami'] and not output_file:
            return []
        else:
            # the rest are probably file names
            return ip.IP.Completer.file_matches(event.symbol)

    return bzr_commands.split()

ip.set_hook('complete_command', bzr_completer, str_key = 'bzr')


def runlistpy(self, event):
    comps = shlex.split(event.line)
    relpath = (len(comps) > 1 and comps[-1] or '')
   
    #print "rp",relpath  # dbg
    lglob = glob.glob
    isdir = os.path.isdir
    if relpath.startswith('~'):
        relpath = os.path.expanduser(relpath)
    dirs = [f.replace('\\','/') + "/" for f in lglob(relpath+'*')
            if isdir(f)]
    pys =  [f.replace('\\','/') for f in lglob(relpath+'*.py')]
    return dirs + pys

ip.set_hook('complete_command', runlistpy, str_key = '%run')

def cd_completer(self, event):
    relpath = event.symbol
    #print event # dbg
    if '-b' in event.line:
        # return only bookmark completions
        bkms = self.db.get('bookmarks',{})
        return bkms.keys()
    
    
    if event.symbol == '-':
        # jump in directory history by number
        ents = ['-%d [%s]' % (i,s) for i,s in enumerate(ip.user_ns['_dh'])]
        if len(ents) > 1:
            return ents
        return []
        
    if relpath.startswith('~'):
        relpath = os.path.expanduser(relpath).replace('\\','/')
    found = []
    for d in [f.replace('\\','/') + '/' for f in glob.glob(relpath+'*') 
              if os.path.isdir(f)]:	
        if ' ' in d:
            # we don't want to deal with any of that, complex code
            # for this is elsewhere
            raise IPython.ipapi.TryNext
        found.append( d )

    if not found:
        if os.path.isdir(relpath):
            return [relpath]
    	raise IPython.ipapi.TryNext
    return found

ip.set_hook('complete_command', cd_completer, str_key = '%cd')
