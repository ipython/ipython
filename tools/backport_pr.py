"""
Backport pull requests to a particular branch.

Usage: backport_pr.py branch PR

e.g.:

    backport_pr.py 0.13.1 123

to backport PR #123 onto branch 0.13.1

"""

from __future__ import print_function

import os
import sys
from subprocess import Popen, PIPE, check_call, check_output
from urllib import urlopen

from gh_api import get_pull_request

def find_rejects(root='.'):
    for dirname, dirs, files in os.walk(root):
        for fname in files:
            if fname.endswith('.rej'):
                yield os.path.join(dirname, fname)

def get_current_branch():
    branches = check_output(['git', 'branch'])
    for branch in branches.splitlines():
        if branch.startswith('*'):
            return branch[1:].strip()

def backport_pr(branch, num, project='ipython/ipython'):
    current_branch = get_current_branch()
    if branch != current_branch:
        check_call(['git', 'checkout', branch])
    pr = get_pull_request(project, num)
    patch_url = pr['patch_url']
    title = pr['title']
    description = pr['body']
    fname = "PR%i.patch" % num
    if os.path.exists(fname):
        print("using patch from {fname}".format(**locals()))
        with open(fname) as f:
            patch = f.read()
    else:
        req = urlopen(patch_url)
        patch = req.read()
    
    msg = "Backport PR #%i: %s" % (num, title) + '\n\n' + description
    check = Popen(['git', 'apply', '--check', '--verbose'], stdin=PIPE)
    a,b = check.communicate(patch)
    
    if check.returncode:
        print("patch did not apply, saving to {fname}".format(**locals()))
        print("edit {fname} until `cat {fname} | git apply --check` succeeds".format(**locals()))
        print("then run tools/backport_pr.py {num} again".format(**locals()))
        if not os.path.exists(fname):
            with open(fname, 'wb') as f:
                f.write(patch)
        return 1
    
    p = Popen(['git', 'apply'], stdin=PIPE)
    a,b = p.communicate(patch)

    commit = Popen(['git', 'commit', '-a', '-m', msg])
    commit.communicate()
    if commit.returncode:
        print("commit failed!")
        return 1
    else:
        print("PR #%i applied, with msg:" % num)
        print()
        print(msg)
        print()
    
    if branch != current_branch:
        check_call(['git', 'checkout', current_branch])
    
    return 0

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    sys.exit(backport_pr(sys.argv[1], int(sys.argv[2])))
