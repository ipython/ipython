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

# TODO: Replacement for this?
from distutils.command.build_scripts import build_scripts
from setuptools.command.install import install
from setuptools.command.install_scripts import install_scripts

from setupext import install_data_ext
from pathlib import Path

#-------------------------------------------------------------------------------
# Useful globals and utility functions
#-------------------------------------------------------------------------------

# A few handy globals
repo_root = Path(__file__).parent

def execfile(fname: Path, globs: dict, locs: dict = None) -> None:
    locs = locs or globs
    exec(compile(fname.read_text(), fname, "exec"), globs, locs)

#---------------------------------------------------------------------------
# Basic project information
#---------------------------------------------------------------------------

# release.py contains version, authors, license, url, keywords, etc.

execfile(Path(repo_root, 'IPython','core','release.py'), globals())

# Create a dict with the basic information
# This dict is eventually passed to setup after additional keys are added.
setup_args = dict(
      name             = name,
      version          = version,
      description      = description,
      long_description = long_description,
      author           = author,
      author_email     = author_email,
      url              = url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      classifiers      = classifiers,
      cmdclass         = {'install_data': install_data_ext},
      project_urls={
          'Documentation': 'https://ipython.readthedocs.io/',
          'Funding'      : 'https://numfocus.org/',
          'Source'       : 'https://github.com/ipython/ipython',
          'Tracker'      : 'https://github.com/ipython/ipython/issues',
      }
      )


#---------------------------------------------------------------------------
# Find packages
#---------------------------------------------------------------------------

def find_packages():
    """
    Find all of IPython's packages.
    """
    excludes = ['deathrow', 'quarantine']
    packages = []
    for dir,subdirs,files in os.walk('IPython'):
        package = dir.replace(os.path.sep, '.')
        if any(package.startswith('IPython.'+exc) for exc in excludes):
            # package is to be excluded (e.g. deathrow)
            continue
        if '__init__.py' not in files:
            # not a package
            continue
        packages.append(package)
    return packages

#---------------------------------------------------------------------------
# Find package data
#---------------------------------------------------------------------------

def find_package_data():
    """
    Find IPython's package_data.
    """
    # This is not enough for these things to appear in an sdist.
    # We need to muck with the MANIFEST to get this to work

    package_data = {
        'IPython.core' : ['profile/README*'],
        'IPython.core.tests' : ['*.png', '*.jpg', 'daft_extension/*.py'],
        'IPython.lib.tests' : ['*.wav'],
        'IPython.testing.plugin' : ['*.txt'],
    }

    return package_data


def check_package_data(package_data):
    """verify that package_data globs make sense"""
    print("checking package data")
    for pkg, data in package_data.items():
        pkg_root = Path(*pkg.split('.'))
        for d in data:
            path = Path(pkg_root, d)
            if '*' in str(path):
                assert len(glob(str(path))) > 0, "No files match pattern %s" % path
            else:
                assert path.exists(), "Missing package data: %s" % path


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
        manpagebase = Path('man', 'man1')
    else:
        manpagebase = Path('share', 'man', 'man1')

    # Simple file lists can be made by hand
    manpages = [f for f in Path('docs', 'man').glob('*.1.gz') if f.is_file()]
    if not manpages:
        # When running from a source tree, the manpages aren't gzipped
        manpages = [f for f in Path('docs', 'man').glob('*.1') if f.is_file()]

    # And assemble the entire output list
    data_files = [ (str(manpagebase), list(map(str, manpages)))]

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
        target_time = Path(target).stat().st_mtime
    except os.error:
        return 1
    for dep in deps:
        dep_time = Path(dep).stat().st_mtime
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
# Find scripts
#---------------------------------------------------------------------------

def find_entry_points():
    """Defines the command line entry points for IPython

    This always uses setuptools-style entry points. When setuptools is not in
    use, our own build_scripts_entrypt class below parses these and builds
    command line scripts.

    Each of our entry points gets both a plain name, e.g. ipython, and one
    suffixed with the Python major version number, e.g. ipython3.
    """
    ep = [
            'ipython%s = IPython:start_ipython',
            'iptest%s = IPython.testing.iptestcontroller:main',
        ]
    suffix = str(sys.version_info[0])
    return [e % '' for e in ep] + [e % suffix for e in ep]

script_src = """#!{executable}
# This script was automatically generated by setup.py
if __name__ == '__main__':
    from {mod} import {func}
    {func}()
"""

class build_scripts_entrypt(build_scripts):
    """Build the command line scripts

    Parse setuptools style entry points and write simple scripts to run the
    target functions.

    On Windows, this also creates .cmd wrappers for the scripts so that you can
    easily launch them from a command line.
    """
    def run(self):
        self.mkpath(self.build_dir)
        outfiles = []
        for script in find_entry_points():
            name, entrypt = script.split('=')
            name = name.strip()
            entrypt = entrypt.strip()
            outfile = Path(self.build_dir) / name
            outfiles.append(outfile)
            print('Writing script to', outfile)

            mod, func = entrypt.split(':')
            outfile.write_text(script_src.format(executable=sys.executable,
                                        mod=mod, func=func))

            if sys.platform == 'win32':
                # Write .cmd wrappers for Windows so 'ipython' etc. work at the
                # command line
                cmd_file = Path(self.build_dir, name + '.cmd')
                cmd = r'@"{python}" "%~dp0\{script}" %*\r\n'.format(
                        python=sys.executable, script=name)
                log.info("Writing %s wrapper script" % cmd_file)
                cmd_file.write_text(cmd)

        outfile_strings = list(map(str, outfiles))
        return outfile_strings, outfile_strings

class install_lib_symlink(Command):
    user_options = [
        ('install-dir=', 'd', "directory to install to"),
        ]

    def initialize_options(self):
        self.install_dir = None

    def finalize_options(self):
        self.set_undefined_options('symlink',
                                   ('install_lib', 'install_dir'),
                                  )

    def run(self):
        if sys.platform == 'win32':
            raise Exception("This doesn't work on Windows.")
        pkg = Path.cwd() / 'IPython'
        dest = Path(self.install_dir) / 'IPython'
        if dest.is_symlink():
            print('removing existing symlink at %s' % dest)
            dest.unlink()
        print('symlinking %s -> %s' % (pkg, dest))
        pkg.symlink_to(dest)

class unsymlink(install):
    def run(self):
        dest = Path(self.install_lib, 'IPython')
        if dest.is_symlink():
            print('removing symlink at %s' % dest)
            dest.unlink()
        else:
            print('No symlink exists at %s' % dest)

class install_symlinked(install):
    def run(self):
        if sys.platform == 'win32':
            raise Exception("This doesn't work on Windows.")

        # Run all sub-commands (at least those that need to be run)
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

    # 'sub_commands': a list of commands this command might have to run to
    # get its work done.  See cmd.py for more info.
    sub_commands = [('install_lib_symlink', lambda self:True),
                    ('install_scripts_sym', lambda self:True),
                   ]

class install_scripts_for_symlink(install_scripts):
    """Redefined to get options from 'symlink' instead of 'install'.

    I love distutils almost as much as I love setuptools.
    """
    def finalize_options(self):
        self.set_undefined_options('build', ('build_scripts', 'build_dir'))
        self.set_undefined_options('symlink',
                                   ('install_scripts', 'install_dir'),
                                   ('force', 'force'),
                                   ('skip_build', 'skip_build'),
                                  )


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

            out_pth = Path(base_dir, pkg_dir, 'utils', '_sysinfo.py')
            if out_pth.is_file() and not repo_commit:
                # nothing to write, don't clobber
                return

            print("writing git commit '%s' to %s" % (repo_commit, out_pth))

            # remove to avoid overwriting original via hard link
            try:
                out_pth.unlink()
            except (IOError, OSError):
                pass

            out_pth.write_text(
                    '# GENERATED BY setup.py\n'
                    'commit = u"%s"\n' % repo_commit)

    return MyBuildPy

