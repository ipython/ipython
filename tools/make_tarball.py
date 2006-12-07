import os,sys,shutil

repo = "http://ipython.scipy.org/svn/ipython/ipython/trunk"
basename = 'ipython'
workdir = './mkdist'

workdir = os.path.abspath(workdir)

print "working at",workdir
def oscmd(c):
    print ">",c
    s = os.system(c)
    if s:
        print "Error",s
        sys.exit(s)


assert not os.path.isdir(workdir)
os.mkdir(workdir)
os.chdir(workdir)

oscmd('svn co %s %s' % (repo,basename))
ver = os.popen('svnversion %s' % basename).read().strip()
tarname = '%s.r%s.tgz' % (basename, ver)
oscmd('tar czvf ../%s %s' % (tarname, basename))
print "Produced: ",os.path.abspath('../' + tarname)
shutil.rmtree(workdir)
