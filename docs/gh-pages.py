#!/usr/bin/env python
"""Script to commit the doc build outputs into the github-pages repo.

Use:

  gh-pages.py [tag]

If no tag is given, the current output of 'git describe' is used.  If given,
that is how the resulting directory will be named.

In practice, you should use either actual clean tags from a current build or
something like 'current' as a stable URL for the most current version of the """

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import os
import re
import shutil
import sys
from os import chdir as cd
from os.path import join as pjoin

from subprocess import Popen, PIPE, CalledProcessError, check_call

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

pages_dir = 'gh-pages'
html_dir = 'build/html'
pdf_dir = 'build/latex'
pages_repo = 'git@github.com:ipython/ipython-doc.git'

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def sh(cmd):
    """Execute command in a subshell, return status code."""
    return check_call(cmd, shell=True)


def sh2(cmd):
    """Execute command in a subshell, return stdout.

    Stderr is unbuffered from the subshell.x"""
    p = Popen(cmd, stdout=PIPE, shell=True)
    out = p.communicate()[0]
    retcode = p.returncode
    if retcode:
        raise CalledProcessError(retcode, cmd)
    else:
        return out.rstrip()


def sh3(cmd):
    """Execute command in a subshell, return stdout, stderr

    If anything appears in stderr, print it out to sys.stderr"""
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = p.communicate()
    retcode = p.returncode
    if retcode:
        raise CalledProcessError(retcode, cmd)
    else:
        return out.rstrip(), err.rstrip()


def init_repo(path):
    """clone the gh-pages repo if we haven't already."""
    sh("git clone %s %s"%(pages_repo, path))
    here = os.getcwd()
    cd(path)
    sh('git checkout gh-pages')
    cd(here)


def render_rstindex(fname, tag, desc=None):
    if desc is None:
        desc = tag
        
    rel = '* {d}: `HTML <{t}/index.html>`_ and `PDF <{t}/ipython.pdf>`_.'.format(t=tag,d=desc)
    rep = re.compile(r'\.\. release')
    out = []
    with file(fname) as f:
        contents = f.read()
    lines = contents.splitlines()
    if rel in contents:
        out = lines
    else:
        for line in lines:
            out.append(line)
            if rep.search(line):
                out.append(rep.sub(rel, line))
    return '\n'.join(out)+'\n'


def new_rstindex(fname, tag, desc=None):
    new_page = render_rstindex(fname, tag, desc)
    os.rename(fname, fname+'~')
    with file(fname, 'w') as f:
        f.write(new_page)


#-----------------------------------------------------------------------------
# Script starts
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    # The tag can be given as a positional argument
    try:
        tag = sys.argv[1]
    except IndexError:
        tag = sh2('git describe')
    
    try:
        desc = sys.argv[2]
    except IndexError:
        desc="Release (%s)"%tag
    
    startdir = os.getcwd()
    if not os.path.exists(pages_dir):
        # init the repo
        init_repo(pages_dir)
    else:
        # ensure up-to-date before operating
        cd(pages_dir)
        sh('git checkout gh-pages')
        sh('git pull')
        cd(startdir)

    dest = pjoin(pages_dir, tag)

    # don't `make html` here, because gh-pages already depends on html in Makefile
    # sh('make html')

    # This is pretty unforgiving: we unconditionally nuke the destination
    # directory, and then copy the html tree in there
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(html_dir, dest)
    shutil.copy(pjoin(pdf_dir, 'ipython.pdf'), pjoin(dest, 'ipython.pdf'))

    try:
        cd(pages_dir)
        status = sh2('git status | head -1')
        branch = re.match('\# On branch (.*)$', status).group(1)
        if branch != 'gh-pages':
            e = 'On %r, git branch is %r, MUST be "gh-pages"' % (pages_dir,
                                                                 branch)
            raise RuntimeError(e)

        sh('git add %s' % tag)
        new_rstindex('index.rst', tag, desc)
        sh('python build_index.py')
        sh('git add index.rst index.html')
        sh('git commit -m"Created new doc release, named: %s"' % tag)
        print
        print 'Most recent 3 commits:'
        sys.stdout.flush()
        sh('git --no-pager log --oneline HEAD~3..')
    finally:
        cd(startdir)

    print
    print 'Now verify the build in: %r' % dest
    print "If everything looks good, 'git push'"
