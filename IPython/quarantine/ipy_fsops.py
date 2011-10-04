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

from IPython.core import ipapi
from IPython.core.error import TryNext
ip = ipapi.get()

import shutil,os,shlex
from IPython.external import mglob
from IPython.external.path import path
from IPython.core.error import UsageError
import IPython.utils.generics

def parse_args(args):
    """ Given arg string 'CMD files... target', return ([files], target) """

    tup = args.split(None, 1)
    if len(tup) == 1:
        raise UsageError("Expected arguments for " + tup[0])

    tup2 = shlex.split(tup[1])

    flist, trg = mglob.expand(tup2[0:-1]), tup2[-1]
    if not flist:
        raise UsageError("No files found:" + str(tup2[0:-1]))
    return flist, trg

def icp(ip,arg):
    """ icp files... targetdir

    Copy all files to target, creating dirs for target if necessary

    icp srcdir dstdir

    Copy srcdir to distdir

    """
    import distutils.dir_util

    fs, targetdir = parse_args(arg)
    if not os.path.isdir(targetdir) and len(fs) > 1:
        distutils.dir_util.mkpath(targetdir,verbose =1)
    for f in fs:
        if os.path.isdir(f):
            shutil.copytree(f, targetdir)
        else:
            shutil.copy2(f,targetdir)
    return fs
ip.define_alias("icp",icp)

def imv(ip,arg):
    """ imv src tgt

    Move source to target.
    """

    fs, target = parse_args(arg)
    if len(fs) > 1:
        assert os.path.isdir(target)
    for f in fs:
        shutil.move(f, target)
    return fs
ip.define_alias("imv",imv)

def irm(ip,arg):
    """ irm path[s]...

    Remove file[s] or dir[s] path. Dirs are deleted recursively.
    """
    try:
        paths = mglob.expand(arg.split(None,1)[1])
    except IndexError:
        raise UsageError("%irm paths...")
    import distutils.dir_util
    for p in paths:
        print "rm",p
        if os.path.isdir(p):
            distutils.dir_util.remove_tree(p, verbose = 1)
        else:
            os.remove(p)

ip.define_alias("irm",irm)

def imkdir(ip,arg):
    """ imkdir path

    Creates dir path, and all dirs on the road
    """
    import distutils.dir_util
    targetdir = arg.split(None,1)[1]
    distutils.dir_util.mkpath(targetdir,verbose =1)

ip.define_alias("imkdir",imkdir)

def igrep(ip,arg):
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

ip.define_alias("igrep",igrep)

def collect(ip,arg):
    """ collect foo/a.txt rec:bar=*.py

    Copies foo/a.txt to ~/_ipython/collect/foo/a.txt and *.py from bar,
    likewise

    Without args, try to open ~/_ipython/collect dir (in win32 at least).
    """
    from IPython.external.path import path
    basedir = path(ip.ipython_dir + '/collect')
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

ip.define_alias("collect",collect)

def inote(ip,arg):
    """ inote Hello world

    Adds timestamp and Hello world to ~/_ipython/notes.txt

    Without args, opens notes.txt for editing.
    """
    import time
    fname = ip.ipython_dir + '/notes.txt'

    try:
        entry = " === " + time.asctime() + ': ===\n' + arg.split(None,1)[1] + '\n'
        f= open(fname, 'a').write(entry)
    except IndexError:
        ip.hooks.editor(fname)

ip.define_alias("inote",inote)

def pathobj_mangle(p):
    return p.replace(' ', '__').replace('.','DOT')
def pathobj_unmangle(s):
    return s.replace('__',' ').replace('DOT','.')



class PathObj(path):
    def __init__(self,p):
        self.path = p
        if p != '.':
            self.ents = [pathobj_mangle(ent) for ent in os.listdir(p)]
        else:
            self.ents = None
    def __complete__(self):
        if self.path != '.':
            return self.ents
        self.ents = [pathobj_mangle(ent) for ent in os.listdir('.')]
        return self.ents
    def __getattr__(self,name):
        if name in self.ents:
            if self.path.endswith('/'):
                sep = ''
            else:
                sep = '/'

            tgt = self.path + sep + pathobj_unmangle(name)
            #print "tgt",tgt
            if os.path.isdir(tgt):
                return PathObj(tgt)
            if os.path.isfile(tgt):
                return path(tgt)

        raise AttributeError, name  # <<< DON'T FORGET THIS LINE !!
    def __str__(self):
        return self.path

    def __repr__(self):
        return "<PathObj to %s>" % self.path

    def __call__(self):
        print "cd:",self.path
        os.chdir(self.path)

def complete_pathobj(obj, prev_completions):
    if hasattr(obj,'__complete__'):
        res = obj.__complete__()
        if res:
            return res
    # just return normal attributes of 'path' object if the dir is empty
    raise TryNext

complete_pathobj = IPython.utils.generics.complete_object.when_type(PathObj)(complete_pathobj)

def test_pathobj():
    #p = PathObj('c:/prj')
    #p2 = p.cgi
    #print p,p2
    rootdir = PathObj("/")
    startmenu = PathObj("d:/Documents and Settings/All Users/Start Menu/Programs")
    cwd = PathObj('.')
    ip.push("rootdir startmenu cwd")

#test_pathobj()