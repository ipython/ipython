#!/usr/bin/env python
""" A script/util to upgrade all files in a directory

This is rather conservative in its approach, only copying/overwriting
new and unedited files.

To be used by "upgrade" feature.
"""
try:
    from IPython.external.path import path
except ImportError:
    from path import path

import hashlib, pickle

def showdiff(old,new):
    import difflib
    d = difflib.Differ()
    lines = d.compare(old.lines(),new.lines())
    realdiff = False
    for l in lines:
        print l,
        if not realdiff and not l[0].isspace():
            realdiff = True
    return realdiff

def upgrade_dir(srcdir, tgtdir):
    """ Copy over all files in srcdir to tgtdir w/ native line endings

    Creates .upgrade_report in tgtdir that stores md5sums of all files
    to notice changed files b/w upgrades.
    """

    def pr(s):
        print s
    junk = ['.svn','ipythonrc*','*.pyc', '*.pyo', '*~', '.hg']
    
    def ignorable(p):
        for pat in junk:
            if p.startswith(pat) or p.fnmatch(pat):
                return True
        return False

    modded = []
    files = [path(srcdir).relpathto(p) for p in path(srcdir).walkfiles()]
    #print files
    rep = tgtdir / '.upgrade_report'
    try:
        rpt = pickle.load(rep.open())
    except:
        rpt = {}

    for f in files:
        if ignorable(f):
            continue
        src = srcdir / f
        tgt = tgtdir / f
        if not tgt.isfile():
            pr("Creating %s" % str(tgt))

            tgt.write_text(src.text())
            rpt[str(tgt)] = hashlib.md5(tgt.text()).hexdigest()
        else:
            cont = tgt.text()
            sum = rpt.get(str(tgt), None)
            #print sum
            if sum and hashlib.md5(cont).hexdigest() == sum:
                pr("%s: Unedited, installing new version" % tgt)
                tgt.write_text(src.text())
                rpt[str(tgt)] = hashlib.md5(tgt.text()).hexdigest()
            else:
                pr(' == Modified, skipping %s, diffs below == ' % tgt)
                #rpt[str(tgt)] = hashlib.md5(tgt.bytes()).hexdigest()
                real = showdiff(tgt,src)
                pr('') # empty line
                if not real:
                    pr("(Ok, it was identical, only upgrading checksum)")
                    rpt[str(tgt)] = hashlib.md5(tgt.text()).hexdigest()
                else:
                    modded.append(tgt)

        #print rpt
    pickle.dump(rpt, rep.open('w'))
    if modded:
        print "\n\nDelete the following files manually (and rerun %upgrade)\nif you need a full upgrade:"
        for m in modded:
            print m


import sys
if __name__ == "__main__":
    upgrade_dir(path(sys.argv[1]), path(sys.argv[2]))
