import os

repo = "http://ipython.scipy.org/svn/ipython/trunk"
basename = 'ipython'
workdir = './mkdist'

workdir = os.path.abspath(workdir)
def oscmd(c):
    print ">",c
    os.system(c)


assert not os.path.isdir(workdir)
os.mkdir(workdir)
os.chdir(workdir)

oscmd('svn co %s %s' % (repo,basename))
ver = os.popen('svnversion %s' % basename)
tarname = '%s.r%s.tgz' % (basename, ver)
oscmd('tar czvf %s %s' % (tarname, basename))
shutil.rmtree(workdir)
