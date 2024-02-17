# encoding: utf-8
"""
This module defines the things that are used in setup.py for building IPython

This includes:

    * The basic arguments to setup
    * Functions for finding things like packages, package data, etc.
    * A function for checking dependencies.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import re
import sys
from glob import glob
from logging import log

from setuptools import Command
from setuptools.command.build_py import build_py

from setuptools.command.install import install
from setuptools.command.install_scripts import install_scripts


#-------------------------------------------------------------------------------
# Useful globals and utility functions
#-------------------------------------------------------------------------------

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join
repo_root = os.path.dirname(os.path.abspath(__file__))

def execfile(fname, globs, locs=None):
    locs = locs or globs
    with open(fname, encoding="utf-8") as f:
        exec(compile(f.read(), fname, "exec"), globs, locs)

# A little utility we'll need below, since glob() does NOT allow you to do
# exclusion on multiple endings!
def file_doesnt_endwith(test,endings):
    """Return true if test is a file and its name does NOT end with any
    of the strings listed in endings."""
    if not isfile(test):
        return False
    for e in endings:
        if test.endswith(e):
            return False
    return True

#---------------------------------------------------------------------------
# Basic project information
#---------------------------------------------------------------------------

# release.py contains version, authors, license, url, keywords, etc.
execfile(pjoin(repo_root, 'IPython','core','release.py'), globals())

# Create a dict with the basic information
# This dict is eventually passed to setup after additional keys are added.
setup_args = dict(
      author           = author,
      author_email     = author_email,
      license          = license,
      )

#---------------------------------------------------------------------------
# Check package data
#---------------------------------------------------------------------------

def check_package_data(package_data):
    """verify that package_data globs make sense"""
    print("checking package data")
    for pkg, data in package_data.items():
        pkg_root = pjoin(*pkg.split('.'))
        for d in data:
            path = pjoin(pkg_root, d)
            if '*' in path:
                assert len(glob(path)) > 0, "No files match pattern %s" % path
            else:
                assert os.path.exists(path), "Missing package data: %s" % path


def check_package_data_first(command):
    """decorator for checking package_data before running a given command

    Probably only needs to wrap build_py
    """
    class DecoratedCommand(command):
        def run(self):
            check_package_data(self.package_data)
            command.run(self)
    return DecoratedCommand


#---------------------------------------------------------------------------
# Find data files
#---------------------------------------------------------------------------

def find_data_files():
    """
    Find IPython's data_files.

    Just man pages at this point.
    """

    if "freebsd" in sys.platform:
        manpagebase = pjoin('man', 'man1')
    else:
        manpagebase = pjoin('share', 'man', 'man1')

    # Simple file lists can be made by hand
    manpages = [f for f in glob(pjoin('docs','man','*.1.gz')) if isfile(f)]
    if not manpages:
        # When running from a source tree, the manpages aren't gzipped
        manpages = [f for f in glob(pjoin('docs','man','*.1')) if isfile(f)]

    # And assemble the entire output list
    data_files = [ (manpagebase, manpages) ]

    return data_files


# The two functions below are copied from IPython.utils.path, so we don't need
# to import IPython during setup, which fails on Python 3.

def target_outdated(target,deps):
    """Determine whether a target is out of date.

    target_outdated(target,deps) -> 1/0

    deps: list of filenames which MUST exist.
    target: single filename which may or may not exist.

    If target doesn't exist or is older than any file listed in deps, return
    true, otherwise return false.
    """
    try:
        target_time = os.path.getmtime(target)
    except os.error:
        return 1
    for dep in deps:
        dep_time = os.path.getmtime(dep)
        if dep_time > target_time:
            #print "For target",target,"Dep failed:",dep # dbg
            #print "times (dep,tar):",dep_time,target_time # dbg
            return 1
    return 0


def target_update(target,deps,cmd):
    """Update a target with a given command given a list of dependencies.

    target_update(target,deps,cmd) -> runs cmd if target is outdated.

    This is just a wrapper around target_outdated() which calls the given
    command if target is outdated."""

    if target_outdated(target,deps):
        os.system(cmd)

#---------------------------------------------------------------------------
# VCS related
#---------------------------------------------------------------------------

def git_prebuild(pkg_dir, build_cmd=build_py):
    """Return extended build or sdist command class for recording commit

    records git commit in IPython.utils._sysinfo.commit

    for use in IPython.utils.sysinfo.sys_info() calls after installation.
    """

    class MyBuildPy(build_cmd):
        ''' Subclass to write commit data into installation tree '''
        def run(self):
            # loose as `.dev` is suppose to be invalid
            print("check version number")
            loose_pep440re = re.compile(r'^(\d+)\.(\d+)\.(\d+((a|b|rc)\d+)?)(\.post\d+)?(\.dev\d*)?$')
            if not loose_pep440re.match(version):
                raise ValueError("Version number '%s' is not valid (should match [N!]N(.N)*[{a|b|rc}N][.postN][.devN])" % version)


            build_cmd.run(self)
            # this one will only fire for build commands
            if hasattr(self, 'build_lib'):
                self._record_commit(self.build_lib)

        def make_release_tree(self, base_dir, files):
            # this one will fire for sdist
            build_cmd.make_release_tree(self, base_dir, files)
            self._record_commit(base_dir)

        def _record_commit(self, base_dir):
            import subprocess
            proc = subprocess.Popen('git rev-parse --short HEAD',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            repo_commit, _ = proc.communicate()
            repo_commit = repo_commit.strip().decode("ascii")

            out_pth = pjoin(base_dir, pkg_dir, 'utils', '_sysinfo.py')
            if os.path.isfile(out_pth) and not repo_commit:
                # nothing to write, don't clobber
                return

            print("writing git commit '%s' to %s" % (repo_commit, out_pth))

            # remove to avoid overwriting original via hard link
            try:
                os.remove(out_pth)
            except (IOError, OSError):
                pass
            with open(out_pth, "w", encoding="utf-8") as out_file:
                out_file.writelines(
                    [
                        "# GENERATED BY setup.py\n",
                        'commit = "%s"\n' % repo_commit,
                    ]
                )

    return MyBuildPy

