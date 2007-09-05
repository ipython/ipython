""" File system operations

Contains: Simple variants of normal unix shell commands (icp, imv, irm,
imkdir, igrep).

Some "otherwise handy" utils ('collect' for gathering files to
~/_ipython/collect, 'inote' for collecting single note lines to
~/_ipython/note.txt)

Mostly of use for bare windows installations where cygwin/equivalent is not
installed and you would otherwise need to deal with dos versions of the
commands (that e.g. don't understand / as path separator). These can
do some useful tricks on their own, though (like use 'mglob' patterns).

Not to be confused with ipipe commands (ils etc.) that also start with i.
"""

import IPython.ipapi
ip = IPython.ipapi.get()

import shutil,os,shlex
from IPython.external import mglob
class IpyShellCmdException(Exception):
    pass

def parse_args(args):
    """ Given arg string 'CMD files... target', return ([files], target) """
    
    tup = args.split(None, 1)
    if len(tup) == 1:
        raise IpyShellCmdException("Expected arguments for " + tup[0])
    
    tup2 = shlex.split(tup[1])
    
    flist, trg = mglob.expand(tup2[0:-1]), tup2[-1]
    if not flist:
        raise IpyShellCmdException("No files found:" + str(tup2[0:-1]))
    return flist, trg
    
def icp(arg):
    """ icp files... targetdir
    
    Copy all files to target, creating dirs for target if necessary
    
    icp srcdir dstdir
    
    Copy srcdir to distdir
    
    """
    import distutils.dir_util
    
    fs, targetdir = parse_args(arg)
    if not os.path.isdir(targetdir):
        distutils.dir_util.mkpath(targetdir,verbose =1)
    for f in fs:
        shutil.copy2(f,targetdir)
    return fs
ip.defalias("icp",icp)

def imv(arg):
    """ imv src tgt
    
    Move source to target.
    """
    
    fs, target = parse_args(arg)
    if len(fs) > 1:
        assert os.path.isdir(target)
    for f in fs:        
        shutil.move(f, target)
    return fs
ip.defalias("imv",imv)        

def irm(arg):
    """ irm path[s]...
    
    Remove file[s] or dir[s] path. Dirs are deleted recursively.
    """
    paths = mglob.expand(arg.split(None,1)[1])
    import distutils.dir_util
    for p in paths:
        print "rm",p
        if os.path.isdir(p):
            distutils.dir_util.remove_tree(p, verbose = 1)
        else:
            os.remove(p)

ip.defalias("irm",irm)

def imkdir(arg):
    """ imkdir path
    
    Creates dir path, and all dirs on the road
    """
    import distutils.dir_util
    targetdir = arg.split(None,1)[1]
    distutils.dir_util.mkpath(targetdir,verbose =1)    

ip.defalias("imkdir",imkdir)    

def igrep(arg):
    """ igrep PAT files...
    
    Very dumb file scan, case-insensitive.
    
    e.g.
    
    igrep "test this" rec:*.py
    
    """
    elems = shlex.split(arg)
    dummy, pat, fs = elems[0], elems[1], mglob.expand(elems[2:])
    res = []
    for f in fs:
        found = False
        for l in open(f):
            if pat.lower() in l.lower():
                if not found:
                    print "[[",f,"]]"
                    found = True
                    res.append(f)
                print l.rstrip()
    return res

ip.defalias("igrep",igrep)    

def collect(arg):
    """ collect foo/a.txt rec:bar=*.py
    
    Copies foo/a.txt to ~/_ipython/collect/foo/a.txt and *.py from bar,
    likewise
    
    Without args, try to open ~/_ipython/collect dir (in win32 at least).
    """
    from path import path
    basedir = path(ip.options.ipythondir + '/collect')
    try:    
        fs = mglob.expand(arg.split(None,1)[1])
    except IndexError:
        os.startfile(basedir)
        return
    for f in fs:
        f = path(f)
        trg = basedir / f.splitdrive()[1].lstrip('/\\')
        if f.isdir():
            print "mkdir",trg
            trg.makedirs()
            continue
        dname = trg.dirname()
        if not dname.isdir():
            dname.makedirs()
        print f,"=>",trg
        shutil.copy2(f,trg)

ip.defalias("collect",collect)            

def inote(arg):
    """ inote Hello world
    
    Adds timestamp and Hello world to ~/_ipython/notes.txt
    
    Without args, opens notes.txt for editing.
    """
    import time
    fname = ip.options.ipythondir + '/notes.txt'
    
    try:
        entry = time.asctime() + ':\n' + arg.split(None,1)[1] + '\n'
        f= open(fname, 'a').write(entry)    
    except IndexError:
        ip.IP.hooks.editor(fname)        

ip.defalias("inote",inote)    
    
