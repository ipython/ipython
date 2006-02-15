""" A script/util to upgrade all files in a directory

This is rather conservative in its approach, only copying/overwriting
new and unedited files.

To be used by "upgrade" feature.
"""
from path import path
import md5,pickle

def showdiff(old,new):
    import difflib
    d = difflib.Differ()
    print "".join(d.compare(old.lines(),new.lines()))

def upgrade_dir(srcdir, tgtdir):
    """ Copy over all files in srcdir to tgtdir w/ native line endings 
    
    Creates .upgrade_report in tgtdir that stores md5sums of all files
    to notice changed files b/w upgrades.
    """

    def pr(s):
        print s

    def ignorable(p):
        
        if p.lower().startswith('.svn') or p.startswith('ipythonrc'):
            return True
        return False
            
        
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
            rpt[str(tgt)] = md5.new(tgt.bytes()).hexdigest()
        else:
            cont = tgt.bytes()
            sum = rpt.get(str(tgt), None)
            #print sum
            if sum and md5.new(cont).hexdigest() == sum:
                pr("Unedited, installing new %s" % tgt)
                rpt[str(tgt)] = md5.new(tgt.bytes()).hexdigest()
            else:
                pr('Modified, skipping %s, diffs below' % tgt)
                #rpt[str(tgt)] = md5.new(tgt.bytes()).hexdigest()
                showdiff(tgt,src)
            pass
        #print rpt
    pickle.dump(rpt, rep.open('w'))
            
import sys
upgrade_dir(path(sys.argv[1]), path(sys.argv[2]))