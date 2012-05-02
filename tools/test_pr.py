"""
This is a script for testing pull requests for IPython. It merges the pull
request with current master, installs and tests on all available versions of
Python, and posts the results to Gist if any tests fail.

Usage:
    python test_pr.py 1657
"""
from __future__ import print_function

import errno
from glob import glob
import json
import os
import shutil
from subprocess import call, check_call, check_output, PIPE, STDOUT, CalledProcessError
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

basedir = os.path.join(os.path.expanduser("~"), ".ipy_pr_tests")
repodir = os.path.join(basedir, "ipython")
ipy_repository = 'git://github.com/ipython/ipython.git'

supported_pythons = ['python2.6', 'python2.7', 'python3.1', 'python3.2']
unavailable_pythons = []

def available_python_versions():
    """Get the executable names of available versions of Python on the system.
    """
    del unavailable_pythons[:]
    for py in supported_pythons:
        try:
            check_call([py, '-c', 'import nose'], stdout=PIPE)
            yield py
        except (OSError, CalledProcessError):
            unavailable_pythons.append(py)

venvs = []

def setup():
    """Prepare the repository and virtualenvs."""
    global venvs
    
    try:
        os.mkdir(basedir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    os.chdir(basedir)
    
    # Delete virtualenvs and recreate
    for venv in glob('venv-*'):
        shutil.rmtree(venv)
    for py in available_python_versions():
        check_call(['virtualenv', '-p', py, '--system-site-packages', 'venv-%s' % py])
        venvs.append((py, 'venv-%s' % py))
    
    # Check out and update the repository
    if not os.path.exists('ipython'):
        check_call(['git', 'clone', ipy_repository])
    os.chdir(repodir)
    check_call(['git', 'checkout', 'master'])
    check_call(['git', 'pull', ipy_repository, 'master'])
    os.chdir(basedir)

def get_pull_request(num, project="ipython/ipython"):
    url = "https://api.github.com/repos/{project}/pulls/{num}".format(project=project, num=num)
    response = urlopen(url).read().decode('utf-8')
    return json.loads(response)

def merge_branch(repo, branch, owner):
    merged_branch = "%s-%s" % (owner, branch)
    os.chdir(repodir)
    # Delete the branch first
    call(['git', 'branch', '-D', merged_branch])
    check_call(['git', 'checkout', '-b', merged_branch])
    check_call(['git', 'pull', repo, branch])
    os.chdir(basedir)

def run_tests(venv):
    py = os.path.join(basedir, venv, 'bin', 'python')
    print(py)
    os.chdir(repodir)
    check_call([py, 'setup.py', 'install'])
    os.chdir(basedir)
    
    iptest = os.path.join(basedir, venv, 'bin', 'iptest')
    if not os.path.exists(iptest):
        iptest = os.path.join(basedir, venv, 'bin', 'iptest3')
        
    print("\nRunning tests, this typically takes a few minutes...")
    try:
        return True, check_output([iptest], stderr=STDOUT).decode('utf-8')
    except CalledProcessError as e:
        return False, e.output

def post_gist(content, description='IPython test log', filename="results.log"):
    """Post some text to a Gist, and return the URL."""
    post_data = json.dumps({
      "description": description,
      "public": True,
      "files": {
        filename: {
          "content": content
        }
      }
    }).encode('utf-8')
    
    response = urlopen("https://api.github.com/gists", post_data)
    response_data = json.loads(response.read().decode('utf-8'))
    return response_data['html_url']

if __name__ == '__main__':
    import sys
    num = sys.argv[1]
    setup()
    pr = get_pull_request(num)
    merge_branch(repo=pr['head']['repo']['clone_url'], 
                 branch=pr['head']['ref'],
                 owner=pr['head']['repo']['owner']['login'])
    
    results = []
    for py, venv in venvs:
        passed, log = run_tests(venv)
        if passed:
            results.append((py, True, None))
        else:
            gist_url = post_gist(log)
            results.append((py, False, gist_url))
    
    print("\n")
    print("**Test results for commit %s merged into master**" % pr['head']['sha'][:7])
    for py, passed, gist_url in results:
        if passed:
            print(py, ":", "OK")
        else:
            print(py, ":", "Failed")
            print("    Test log:", gist_url)
    print("Not available for testing:", ", ".join(unavailable_pythons))
