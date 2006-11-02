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
import glob,os,shlex

ip = IPython.ipapi.get()

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
    
    global pkg_cache
    import pkgutil,imp,time
    #current = 
    if pkg_cache is None:
        print "\n\n[Standby while scanning modules, this can take a while]\n\n"
        pkg_cache = list(pkgutil.walk_packages())
    
    for ld, name, ispkg in pkg_cache:
        yield name
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
    if len((event.line + 'placeholder').split()) > 2:
        # the rest are probably file names
        return ip.IP.Completer.file_matches(event.symbol)
        
    return svn_commands.split()

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

def runlistpy(self, event):
    comps = shlex.split(event.line)
    relpath = (len(comps) > 1 and comps[-1] or '')
   
    print "rp",relpath
    if relpath.startswith('~'):
        relpath = os.path.expanduser(relpath)
    dirs = [f.replace('\\','/') + "/" for f in  glob.glob(relpath+'*') if os.path.isdir(f)]
    pys =  [f.replace('\\','/') for f in  glob.glob(relpath+'*.py')]
    return dirs + pys

ip.set_hook('complete_command', runlistpy, str_key = '%run')

def cd_completer(self, event):
    relpath = event.symbol
    
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
    found =  [f.replace('\\','/')+'/' for f in glob.glob(relpath+'*') if os.path.isdir(f)]
    if not found:
        return [relpath]
    return found

ip.set_hook('complete_command', cd_completer, str_key = '%cd')