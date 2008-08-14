
""" Implementations for various useful completers

See Extensions/ipy_stock_completers.py on examples of how to enable a completer,
but the basic idea is to do:

ip.set_hook('complete_command', svn_completer, str_key = 'svn')

"""
import IPython.ipapi
import glob,os,shlex,sys
import inspect
from time import time
from zipimport import zipimporter
ip = IPython.ipapi.get()

try:
    set
except:
    from sets import Set as set

TIMEOUT_STORAGE = 3 #Time in seconds after which the rootmodules will be stored
TIMEOUT_GIVEUP = 20 #Time in seconds after which we give up

def quick_completer(cmd, completions):
    """ Easily create a trivial completer for a command.

    Takes either a list of completions, or all completions in string
    (that will be split on whitespace)
    
    Example::
    
        [d:\ipython]|1> import ipy_completers                                       
        [d:\ipython]|2> ipy_completers.quick_completer('foo', ['bar','baz'])        
        [d:\ipython]|3> foo b<TAB>
        bar baz                                                                     
        [d:\ipython]|3> foo ba
    """
    if isinstance(completions, basestring):
        
        completions = completions.split()
    def do_complete(self,event):
        return completions
    
    ip.set_hook('complete_command',do_complete, str_key = cmd)
    
def getRootModules():
    """
    Returns a list containing the names of all the modules available in the
    folders of the pythonpath.
    """
    modules = []
    if ip.db.has_key('rootmodules'):
        return ip.db['rootmodules']
    t = time()
    store = False
    for path in sys.path:
        modules += moduleList(path)        
        if time() - t >= TIMEOUT_STORAGE and not store:
            store = True
            print "\nCaching the list of root modules, please wait!" 
            print "(This will only be done once - type '%rehashx' to " + \
            "reset cache!)"
            print
        if time() - t > TIMEOUT_GIVEUP:
            print "This is taking too long, we give up."
            print
            ip.db['rootmodules'] = []
            return []
    
    modules += sys.builtin_module_names
      
    modules = list(set(modules))
    if '__init__' in modules:
        modules.remove('__init__')
    modules = list(set(modules))
    if store:
        ip.db['rootmodules'] = modules
    return modules

def moduleList(path):
    """
    Return the list containing the names of the modules available in the given
    folder.
    """

    if os.path.isdir(path):
        folder_list = os.listdir(path)
    elif path.endswith('.egg'):
        try:
            folder_list = [f for f in zipimporter(path)._files]
        except:
            folder_list = []
    else:
        folder_list = []
    #folder_list = glob.glob(os.path.join(path,'*'))
    folder_list = [p for p in folder_list  \
       if os.path.exists(os.path.join(path, p,'__init__.py'))\
           or p[-3:] in ('.py','.so')\
           or p[-4:] in ('.pyc','.pyo','.pyd')]

    folder_list = [os.path.basename(p).split('.')[0] for p in folder_list]
    return folder_list

def moduleCompletion(line):
    """
    Returns a list containing the completion possibilities for an import line.
    The line looks like this :
    'import xml.d'
    'from xml.dom import'
    """
    def tryImport(mod, only_modules=False):
        def isImportable(module, attr):
            if only_modules:
                return inspect.ismodule(getattr(module, attr))
            else:
                return not(attr[:2] == '__' and attr[-2:] == '__')
        try:
            m = __import__(mod)
        except:
            return []
        mods = mod.split('.')
        for module in mods[1:]:
            m = getattr(m,module)
        if (not hasattr(m, '__file__')) or (not only_modules) or\
           (hasattr(m, '__file__') and '__init__' in m.__file__):
            completion_list = [attr for attr in dir(m) if isImportable(m, attr)]
        completion_list.extend(getattr(m,'__all__',[]))
        if hasattr(m, '__file__') and '__init__' in m.__file__:
            completion_list.extend(moduleList(os.path.dirname(m.__file__)))
        completion_list = list(set(completion_list))
        if '__init__' in completion_list:
            completion_list.remove('__init__')
        return completion_list

    words = line.split(' ')
    if len(words) == 3 and words[0] == 'from':
        return ['import ']
    if len(words) < 3 and (words[0] in ['import','from']) :
        if len(words) == 1:
            return getRootModules()
        mod = words[1].split('.')
        if len(mod) < 2:
            return getRootModules()
        completion_list = tryImport('.'.join(mod[:-1]), True)
        completion_list = ['.'.join(mod[:-1] + [el]) for el in completion_list]
        return completion_list
    if len(words) >= 3 and words[0] == 'from':
        mod = words[1]
        return tryImport(mod)

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


pkg_cache = None

def module_completer(self,event):
    """ Give completions after user has typed 'import ...' or 'from ...'"""

    # This works in all versions of python.  While 2.5 has
    # pkgutil.walk_packages(), that particular routine is fairly dangerous,
    # since it imports *EVERYTHING* on sys.path.  That is: a) very slow b) full
    # of possibly problematic side effects.
    # This search the folders in the sys.path for available modules.

    return moduleCompletion(event.line)


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
            return ip.IP.Completer.file_matches(event.symbol)

    return bzr_commands()


def shlex_split(x):
    """Helper function to split lines into segments."""
    #shlex.split raise exception if syntax error in sh syntax
    #for example if no closing " is found. This function keeps dropping
    #the last character of the line until shlex.split does not raise
    #exception. Adds end of the line to the result of shlex.split
    #example: %run "c:/python  -> ['%run','"c:/python']
    endofline=[]
    while x!="":
        try:
            comps=shlex.split(x)
            if len(endofline)>=1:
                comps.append("".join(endofline))
            return comps
        except ValueError:
            endofline=[x[-1:]]+endofline
            x=x[:-1]
    return ["".join(endofline)]

def runlistpy(self, event):
    comps = shlex_split(event.line)
    relpath = (len(comps) > 1 and comps[-1] or '').strip("'\"")

    #print "\nev=",event  # dbg
    #print "rp=",relpath  # dbg
    #print 'comps=',comps  # dbg

    lglob = glob.glob
    isdir = os.path.isdir
    if relpath.startswith('~'):
        relpath = os.path.expanduser(relpath)
    dirs = [f.replace('\\','/') + "/" for f in lglob(relpath+'*')
            if isdir(f)]

    # Find if the user has already typed the first filename, after which we
    # should complete on all files, since after the first one other files may
    # be arguments to the input script.
    #filter(
    if filter(lambda f: f.endswith('.py') or f.endswith('.ipy') or
              f.endswith('.pyw'),comps):
        pys =  [f.replace('\\','/') for f in lglob('*')]
    else:
        pys =  [f.replace('\\','/')
                for f in lglob(relpath+'*.py') + lglob(relpath+'*.ipy') +
                lglob(relpath + '*.pyw')]
    return dirs + pys


greedy_cd_completer = False

def cd_completer(self, event):
    relpath = event.symbol
    #print event # dbg
    if '-b' in event.line:
        # return only bookmark completions
        bkms = self.db.get('bookmarks',{})
        return bkms.keys()

    
    if event.symbol == '-':
        width_dh = str(len(str(len(ip.user_ns['_dh']) + 1)))
        # jump in directory history by number
        fmt = '-%0' + width_dh +'d [%s]'
        ents = [ fmt % (i,s) for i,s in enumerate(ip.user_ns['_dh'])]
        if len(ents) > 1:
            return ents
        return []

    if event.symbol.startswith('--'):
        return ["--" + os.path.basename(d) for d in ip.user_ns['_dh']]
    
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


    def single_dir_expand(matches):
        "Recursively expand match lists containing a single dir."
        
        if len(matches) == 1 and os.path.isdir(matches[0]):
            # Takes care of links to directories also.  Use '/'
            # explicitly, even under Windows, so that name completions
            # don't end up escaped.
            d = matches[0]
            if d[-1] in ['/','\\']:
                d = d[:-1]

            subdirs = [p for p in os.listdir(d) if os.path.isdir( d + '/' + p) and not p.startswith('.')]
            if subdirs:
                matches = [ (d + '/' + p) for p in subdirs ]
                return single_dir_expand(matches)
            else:
                return matches
        else:
            return matches

    if greedy_cd_completer:
        return single_dir_expand(found)
    else:
        return found

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

