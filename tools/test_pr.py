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
from gh_api import Obj

basedir = os.path.join(os.path.expanduser("~"), ".ipy_pr_tests")
repodir = os.path.join(basedir, "ipython")
ipy_repository = 'git://github.com/ipython/ipython.git'
ipy_http_repository = 'http://github.com/ipython/ipython.git'
gh_project="ipython/ipython"

supported_pythons = ['python2.6', 'python2.7', 'python3.2']
            
missing_libs_re = re.compile(r"Tools and libraries NOT available at test time:\n"
                             r"\s*(.*?)\n")
def get_missing_libraries(log):
    m = missing_libs_re.search(log)
    if m:
        return m.group(1)

class TestRun(object):
    def __init__(self, pr_num, extra_args):
        self.unavailable_pythons = []
        self.venvs = []
        self.pr_num = pr_num
        self.extra_args = extra_args
        
        self.pr = gh_api.get_pull_request(gh_project, pr_num)
        
        self.setup()
        
        self.results = []
    
    def available_python_versions(self):
        """Get the executable names of available versions of Python on the system.
        """
        for py in supported_pythons:
            try:
                check_call([py, '-c', 'import nose'], stdout=PIPE)
                yield py
            except (OSError, CalledProcessError):
                self.unavailable_pythons.append(py)

    def setup(self):
        """Prepare the repository and virtualenvs."""        
        try:
            os.mkdir(basedir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        os.chdir(basedir)
        
        # Delete virtualenvs and recreate
        for venv in glob('venv-*'):
            shutil.rmtree(venv)
        for py in self.available_python_versions():
            check_call(['virtualenv', '-p', py, '--system-site-packages', 'venv-%s' % py])
            self.venvs.append((py, 'venv-%s' % py))
        
        # Check out and update the repository
        if not os.path.exists('ipython'):
            try :
                check_call(['git', 'clone', ipy_repository])
            except CalledProcessError :
                check_call(['git', 'clone', ipy_http_repository])
        os.chdir(repodir)
        check_call(['git', 'checkout', 'master'])
        try :
            check_call(['git', 'pull', 'origin', 'master'])
        except CalledProcessError :
            check_call(['git', 'pull', ipy_http_repository, 'master'])
        self.master_sha = check_output(['git', 'log', '-1', '--format=%h']).decode('ascii').strip()
        os.chdir(basedir)
    
    def get_branch(self):
        repo = self.pr['head']['repo']['clone_url']
        branch = self.pr['head']['ref']
        owner = self.pr['head']['repo']['owner']['login']
        mergeable = self.pr['mergeable']
        
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
    
    def markdown_format(self):
        def format_result(result):
            s = "* %s: " % result.py
            if result.passed:
                s += "OK"
            else:
                s += "Failed, log at %s" % result.log_url
            if result.missing_libraries:
                s += " (libraries not available: " + result.missing_libraries + ")"
            return s
        
        if self.pr['mergeable']:
            com = self.pr['head']['sha'][:7] + " merged into master (%s)" % self.master_sha
        else:
            com = self.pr['head']['sha'][:7] + " (can't merge cleanly)"
        lines = ["**Test results for commit %s**" % com,
                 "Platform: " + sys.platform,
                 ""] + \
                [format_result(r) for r in self.results] + \
                [""]
        if self.extra_args:
            lines.append("Extra args: %r" % self.extra_args),
        lines.append("Not available for testing: " + ", ".join(self.unavailable_pythons))
        return "\n".join(lines)
    
    def post_results_comment(self):
        body = self.markdown_format()
        gh_api.post_issue_comment(gh_project, self.pr_num, body)
    
    def print_results(self):
        pr = self.pr
        
        print("\n")
        msg = "**Test results for commit %s" % pr['head']['sha'][:7]
        if pr['mergeable']:
            msg += " merged into master (%s)**" % self.master_sha
        else:
            msg += " (can't merge cleanly)**"
        print(msg)
        print("Platform:", sys.platform)
        for result in self.results:
            if result.passed:
                print(result.py, ":", "OK")
            else:
                print(result.py, ":", "Failed")
                print("    Test log:", result.get('log_url') or result.log_file)
            if result.missing_libraries:
                print("    Libraries not available:", result.missing_libraries)
        
        if self.extra_args:
            print("Extra args:", self.extra_args)
        print("Not available for testing:", ", ".join(self.unavailable_pythons))

    def dump_results(self):
        with open(os.path.join(basedir, 'lastresults.pkl'), 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load_results():
        with open(os.path.join(basedir, 'lastresults.pkl'), 'rb') as f:
            return pickle.load(f)

    def save_logs(self):
        for result in self.results:
            if not result.passed:
                result_locn = os.path.abspath(os.path.join('venv-%s' % result.py,
                                            self.pr['head']['sha'][:7]+".log"))
                with io.open(result_locn, 'w', encoding='utf-8') as f:
                    f.write(result.log)
            
                result.log_file = result_locn

    def post_logs(self):
        for result in self.results:
            if not result.passed:
                result.log_url = gh_api.post_gist(result.log,
                                                description='IPython test log',
                                                filename="results.log", auth=True)
    
    def run(self):
        for py, venv in self.venvs:
            tic = time.time()
            passed, log = run_tests(venv, self.extra_args)
            elapsed = int(time.time() - tic)
            print("Ran tests with %s in %is" % (py, elapsed))
            missing_libraries = get_missing_libraries(log)
            
            self.results.append(Obj(py=py,
                                   passed=passed,
                                   log=log,
                                   missing_libraries=missing_libraries
                                  )
                               )


def run_tests(venv, extra_args):
    py = os.path.join(basedir, venv, 'bin', 'python')
    print(py)
    os.chdir(repodir)
    # cleanup build-dir
    if os.path.exists('build'):
        shutil.rmtree('build')
    tic = time.time()
    print ("\nInstalling IPython with %s" % py)
    logfile = os.path.join(basedir, venv, 'install.log')
    print ("Install log at %s" % logfile)
    with open(logfile, 'wb') as f:
        check_call([py, 'setup.py', 'install'], stdout=f)
    toc = time.time()
    print ("Installed IPython in %.1fs" % (toc-tic))
    os.chdir(basedir)
    
    # Environment variables:
    orig_path = os.environ["PATH"]
    os.environ["PATH"] = os.path.join(basedir, venv, 'bin') + ':' + os.environ["PATH"]
    os.environ.pop("PYTHONPATH", None)
    
    # check that the right IPython is imported
    ipython_file = check_output([py, '-c', 'import IPython; print (IPython.__file__)'])
    ipython_file = ipython_file.strip().decode('utf-8')
    if not ipython_file.startswith(os.path.join(basedir, venv)):
        msg = "IPython does not appear to be in the venv: %s" % ipython_file
        msg += "\nDo you use setupegg.py develop?"
        print(msg, file=sys.stderr)
        return False, msg
    
    iptest = os.path.join(basedir, venv, 'bin', 'iptest')
    if not os.path.exists(iptest):
        iptest = os.path.join(basedir, venv, 'bin', 'iptest3')
        
    print("\nRunning tests, this typically takes a few minutes...")
    try:
        return True, check_output([iptest] + extra_args, stderr=STDOUT).decode('utf-8')
    except CalledProcessError as e:
        return False, e.output.decode('utf-8')
    finally:
        # Restore $PATH
        os.environ["PATH"] = orig_path


def test_pr(num, post_results=True, extra_args=None):
    # Get Github authorisation first, so that the user is prompted straight away
    # if their login is needed.
    if post_results:
        gh_api.get_auth_token()
    
    testrun = TestRun(num, extra_args or [])
    
    testrun.get_branch()
    
    testrun.run()

    testrun.dump_results()
    
    testrun.save_logs()
    testrun.print_results()
    
    if post_results:
        testrun.post_logs()
        testrun.post_results_comment()
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
    
    args, extra_args = parser.parse_known_args()
    test_pr(args.number, post_results=args.publish, extra_args=extra_args)
