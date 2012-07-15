#!/usr/bin/env python
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
import io
import json
import os
import pickle
import re
import requests
import shutil
import time
from subprocess import call, check_call, check_output, PIPE, STDOUT, CalledProcessError
import sys

import gh_api

basedir = os.path.join(os.path.expanduser("~"), ".ipy_pr_tests")
repodir = os.path.join(basedir, "ipython")
ipy_repository = 'git://github.com/ipython/ipython.git'
ipy_http_repository = 'http://github.com/ipython/ipython.git'
gh_project="ipython/ipython"

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
        try :
            check_call(['git', 'clone', ipy_repository])
        except CalledProcessError :
            check_call(['git', 'clone', ipy_http_repository])
    os.chdir(repodir)
    check_call(['git', 'checkout', 'master'])
    try :
        check_call(['git', 'pull', ipy_repository, 'master'])
    except CalledProcessError :
        check_call(['git', 'pull', ipy_http_repository, 'master'])
    os.chdir(basedir)

missing_libs_re = re.compile(r"Tools and libraries NOT available at test time:\n"
                             r"\s*(.*?)\n")
def get_missing_libraries(log):
    m = missing_libs_re.search(log)
    if m:
        return m.group(1)

def get_branch(repo, branch, owner, mergeable):
    os.chdir(repodir)
    if mergeable:
        merged_branch = "%s-%s" % (owner, branch)
        # Delete the branch first
        call(['git', 'branch', '-D', merged_branch])
        check_call(['git', 'checkout', '-b', merged_branch])
        check_call(['git', 'pull', '--no-ff', '--no-commit', repo, branch])
        check_call(['git', 'commit', '-m', "merge %s/%s" % (repo, branch)])
    else:
        # Fetch the branch without merging it.
        check_call(['git', 'fetch', repo, branch])
        check_call(['git', 'checkout', 'FETCH_HEAD'])
    os.chdir(basedir)

def run_tests(venv):
    py = os.path.join(basedir, venv, 'bin', 'python')
    print(py)
    os.chdir(repodir)
    # cleanup build-dir
    if os.path.exists('build'):
        shutil.rmtree('build')
    check_call([py, 'setup.py', 'install'])
    os.chdir(basedir)
    
    # Environment variables:
    orig_path = os.environ["PATH"]
    os.environ["PATH"] = os.path.join(basedir, venv, 'bin') + ':' + os.environ["PATH"]
    os.environ.pop("PYTHONPATH", None)
    
    iptest = os.path.join(basedir, venv, 'bin', 'iptest')
    if not os.path.exists(iptest):
        iptest = os.path.join(basedir, venv, 'bin', 'iptest3')
        
    print("\nRunning tests, this typically takes a few minutes...")
    try:
        return True, check_output([iptest], stderr=STDOUT).decode('utf-8')
    except CalledProcessError as e:
        return False, e.output.decode('utf-8')
    finally:
        # Restore $PATH
        os.environ["PATH"] = orig_path

def markdown_format(pr, results_urls, unavailable_pythons):
    def format_result(py, passed, gist_url, missing_libraries):
        s = "* %s: " % py
        if passed:
            s += "OK"
        else:
            s += "Failed, log at %s" % gist_url
        if missing_libraries:
            s += " (libraries not available: " + missing_libraries + ")"
        return s
    
    if pr['mergeable']:
        com = pr['head']['sha'][:7] + " merged into master"
    else:
        com = pr['head']['sha'][:7] + " (can't merge cleanly)"
    lines = ["**Test results for commit %s**" % com,
             "Platform: " + sys.platform,
             ""] + \
            [format_result(*r) for r in results_urls] + \
            ["",
             "Not available for testing: " + ", ".join(unavailable_pythons)] 
    return "\n".join(lines)

def post_results_comment(pr, results, num, unavailable_pythons=unavailable_pythons):
    body = markdown_format(pr, results, unavailable_pythons)
    gh_api.post_issue_comment(gh_project, num, body)

def print_results(pr, results_urls, unavailable_pythons=unavailable_pythons):
    print("\n")
    if pr['mergeable']:
        print("**Test results for commit %s merged into master**" % pr['head']['sha'][:7])
    else:
        print("**Test results for commit %s (can't merge cleanly)**" % pr['head']['sha'][:7])
    print("Platform:", sys.platform)
    for py, passed, gist_url, missing_libraries in results_urls:
        if passed:
            print(py, ":", "OK")
        else:
            print(py, ":", "Failed")
            print("    Test log:", gist_url)
        if missing_libraries:
            print("    Libraries not available:", missing_libraries)
    print("Not available for testing:", ", ".join(unavailable_pythons))

def dump_results(num, results, pr):
    with open(os.path.join(basedir, 'lastresults.pkl'), 'wb') as f:
        pickle.dump((num, results, pr, unavailable_pythons), f)

def load_results():
    with open(os.path.join(basedir, 'lastresults.pkl'), 'rb') as f:
        return pickle.load(f)

def save_logs(results, pr):
    results_paths = []
    for py, passed, log, missing_libraries in results:
        if passed:
            results_paths.append((py, passed, None, missing_libraries))
        else:
            
            result_locn = os.path.abspath(os.path.join('venv-%s' % py,
                                        pr['head']['sha'][:7]+".log"))
            with io.open(result_locn, 'w', encoding='utf-8') as f:
                f.write(log)
        
            results_paths.append((py, False, result_locn, missing_libraries))
    
    return results_paths

def post_logs(results):
    results_urls = []
    for py, passed, log, missing_libraries in results:
        if passed:
            results_urls.append((py, passed, None, missing_libraries))
        else:
            result_locn = gh_api.post_gist(log, description='IPython test log',
                                            filename="results.log", auth=True)
            results_urls.append((py, False, result_locn, missing_libraries))
    
    return results_urls

def test_pr(num, post_results=True):
    # Get Github authorisation first, so that the user is prompted straight away
    # if their login is needed.
    if post_results:
        gh_api.get_auth_token()
    
    setup()
    pr = gh_api.get_pull_request(gh_project, num)
    get_branch(repo=pr['head']['repo']['clone_url'], 
                 branch=pr['head']['ref'],
                 owner=pr['head']['repo']['owner']['login'],
                 mergeable=pr['mergeable'],
              )
    
    results = []
    for py, venv in venvs:
        tic = time.time()
        passed, log = run_tests(venv)
        elapsed = int(time.time() - tic)
        print("Ran tests with %s in %is" % (py, elapsed))
        missing_libraries = get_missing_libraries(log)
        if passed:
            results.append((py, True, None, missing_libraries))
        else:
            results.append((py, False, log, missing_libraries))
    
    dump_results(num, results, pr)
    
    results_paths = save_logs(results, pr)
    print_results(pr, results_paths)
    
    if post_results:
        results_urls = post_logs(results)
        post_results_comment(pr, results_urls, num)
        print("(Posted to Github)")
    else:
        post_script = os.path.join(os.path.dirname(sys.argv[0]), "post_pr_test.py")
        print("To post the results to Github, run", post_script)
    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Test an IPython pull request")
    parser.add_argument('-p', '--publish', action='store_true',
                        help="Publish the results to Github")
    parser.add_argument('number', type=int, help="The pull request number")
    
    args = parser.parse_args()
    test_pr(args.number, post_results=args.publish)
