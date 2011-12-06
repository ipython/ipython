# encoding: utf-8
"""
This module defines the things that are used in setup.py for building IPython

This includes:

    * The basic arguments to setup
    * Functions for finding things like packages, package data, etc.
    * A function for checking dependencies.
"""
from __future__ import print_function

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
import os
import sys

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser
from distutils.command.build_py import build_py
from glob import glob

from setupext import install_data_ext

#-------------------------------------------------------------------------------
# Useful globals and utility functions
#-------------------------------------------------------------------------------

# A few handy globals
isfile = os.path.isfile
pjoin = os.path.join

def oscmd(s):
    print(">", s)
    os.system(s)

try:
    execfile
except NameError:
    def execfile(fname, globs, locs=None):
        locs = locs or globs
        exec(compile(open(fname).read(), fname, "exec"), globs, locs)

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
execfile(pjoin('IPython','core','release.py'), globals())

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
      download_url     = download_url,
      license          = license,
      platforms        = platforms,
      keywords         = keywords,
      classifiers      = classifiers,
      cmdclass         = {'install_data': install_data_ext},
      )


#---------------------------------------------------------------------------
# Find packages
#---------------------------------------------------------------------------

def find_packages():
    """
    Find all of IPython's packages.
    """
    excludes = ['deathrow']
    packages = []
    for dir,subdirs,files in os.walk('IPython'):
        package = dir.replace(os.path.sep, '.')
        if any([ package.startswith('IPython.'+exc) for exc in excludes ]):
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
    
    # exclude static things that we don't ship (e.g. mathjax)
    excludes = ['mathjax']
    
    # add 'static/' prefix to exclusions, and tuplify for use in startswith
    excludes = tuple([os.path.join('static', ex) for ex in excludes])
    
    # walk notebook resources:
    cwd = os.getcwd()
    os.chdir(os.path.join('IPython', 'frontend', 'html', 'notebook'))
    static_walk = list(os.walk('static'))
    os.chdir(cwd)
    static_data = []
    for parent, dirs, files in static_walk:
        if parent.startswith(excludes):
            continue
        for f in files:
            static_data.append(os.path.join(parent, f))

    package_data = {
        'IPython.config.profile' : ['README*', '*/*.py'],
        'IPython.testing' : ['*.txt'],
        'IPython.frontend.html.notebook' : ['templates/*'] + static_data,
        'IPython.frontend.qt.console' : ['resources/icon/*.svg'],
    }
    return package_data


#---------------------------------------------------------------------------
# Find data files
#---------------------------------------------------------------------------

def make_dir_struct(tag,base,out_base):
    """Make the directory structure of all files below a starting dir.

    This is just a convenience routine to help build a nested directory
    hierarchy because distutils is too stupid to do this by itself.

    XXX - this needs a proper docstring!
    """

    # we'll use these a lot below
    lbase = len(base)
    pathsep = os.path.sep
    lpathsep = len(pathsep)

    out = []
    for (dirpath,dirnames,filenames) in os.walk(base):
        # we need to strip out the dirpath from the base to map it to the
        # output (installation) path.  This requires possibly stripping the
        # path separator, because otherwise pjoin will not work correctly
        # (pjoin('foo/','/bar') returns '/bar').

        dp_eff = dirpath[lbase:]
        if dp_eff.startswith(pathsep):
            dp_eff = dp_eff[lpathsep:]
        # The output path must be anchored at the out_base marker
        out_path = pjoin(out_base,dp_eff)
        # Now we can generate the final filenames. Since os.walk only produces
        # filenames, we must join back with the dirpath to get full valid file
        # paths:
        pfiles = [pjoin(dirpath,f) for f in filenames]
        # Finally, generate the entry we need, which is a pari of (output
        # path, files) for use as a data_files parameter in install_data.
        out.append((out_path, pfiles))

    return out


def find_data_files():
    """
    Find IPython's data_files.

    Most of these are docs.
    """

    docdirbase  = pjoin('share', 'doc', 'ipython')
    manpagebase = pjoin('share', 'man', 'man1')

    # Simple file lists can be made by hand
    manpages  = filter(isfile, glob(pjoin('docs','man','*.1.gz')))
    if not manpages:
        # When running from a source tree, the manpages aren't gzipped
        manpages = filter(isfile, glob(pjoin('docs','man','*.1')))
    igridhelpfiles = filter(isfile,
                            glob(pjoin('IPython','extensions','igrid_help.*')))

    # For nested structures, use the utility above
    example_files = make_dir_struct(
        'data',
        pjoin('docs','examples'),
        pjoin(docdirbase,'examples')
    )
    manual_files = make_dir_struct(
        'data',
        pjoin('docs','html'),
        pjoin(docdirbase,'manual')
    )

    # And assemble the entire output list
    data_files = [ (manpagebase, manpages),
                   (pjoin(docdirbase, 'extensions'), igridhelpfiles),
                   ] + manual_files + example_files

    return data_files


def make_man_update_target(manpage):
    """Return a target_update-compliant tuple for the given manpage.

    Parameters
    ----------
    manpage : string
      Name of the manpage, must include the section number (trailing number).

    Example
    -------

    >>> make_man_update_target('ipython.1') #doctest: +NORMALIZE_WHITESPACE
    ('docs/man/ipython.1.gz',
     ['docs/man/ipython.1'],
     'cd docs/man && gzip -9c ipython.1 > ipython.1.gz')
    """
    man_dir = pjoin('docs', 'man')
    manpage_gz = manpage + '.gz'
    manpath = pjoin(man_dir, manpage)
    manpath_gz = pjoin(man_dir, manpage_gz)
    gz_cmd = ( "cd %(man_dir)s && gzip -9c %(manpage)s > %(manpage_gz)s" %
               locals() )
    return (manpath_gz, [manpath], gz_cmd)

#---------------------------------------------------------------------------
# Find scripts
#---------------------------------------------------------------------------

def find_scripts(entry_points=False, suffix=''):
    """Find IPython's scripts.

    if entry_points is True:
        return setuptools entry_point-style definitions
    else:
        return file paths of plain scripts [default]

    suffix is appended to script names if entry_points is True, so that the
    Python 3 scripts get named "ipython3" etc.
    """
    if entry_points:
        console_scripts = [s % suffix for s in [
            'ipython%s = IPython.frontend.terminal.ipapp:launch_new_instance',
            'pycolor%s = IPython.utils.PyColorize:main',
            'ipcontroller%s = IPython.parallel.apps.ipcontrollerapp:launch_new_instance',
            'ipengine%s = IPython.parallel.apps.ipengineapp:launch_new_instance',
            'iplogger%s = IPython.parallel.apps.iploggerapp:launch_new_instance',
            'ipcluster%s = IPython.parallel.apps.ipclusterapp:launch_new_instance',
            'iptest%s = IPython.testing.iptest:main',
            'irunner%s = IPython.lib.irunner:main'
        ]]
        gui_scripts = [s % suffix for s in [
            'ipython%s-qtconsole = IPython.frontend.qt.console.qtconsoleapp:main',
        ]]
        scripts = dict(console_scripts=console_scripts, gui_scripts=gui_scripts)
    else:
        parallel_scripts = pjoin('IPython','parallel','scripts')
        main_scripts = pjoin('IPython','scripts')
        scripts = [
                   pjoin(parallel_scripts, 'ipengine'),
                   pjoin(parallel_scripts, 'ipcontroller'),
                   pjoin(parallel_scripts, 'ipcluster'),
                   pjoin(parallel_scripts, 'iplogger'),
                   pjoin(main_scripts, 'ipython'),
                   pjoin(main_scripts, 'pycolor'),
                   pjoin(main_scripts, 'irunner'),
                   pjoin(main_scripts, 'iptest')
        ]
    return scripts

#---------------------------------------------------------------------------
# Verify all dependencies
#---------------------------------------------------------------------------

def check_for_dependencies():
    """Check for IPython's dependencies.

    This function should NOT be called if running under setuptools!
    """
    from setupext.setupext import (
        print_line, print_raw, print_status,
        check_for_sphinx, check_for_pygments,
        check_for_nose, check_for_pexpect,
        check_for_pyzmq, check_for_readline
    )
    print_line()
    print_raw("BUILDING IPYTHON")
    print_status('python', sys.version)
    print_status('platform', sys.platform)
    if sys.platform == 'win32':
        print_status('Windows version', sys.getwindowsversion())

    print_raw("")
    print_raw("OPTIONAL DEPENDENCIES")

    check_for_sphinx()
    check_for_pygments()
    check_for_nose()
    check_for_pexpect()
    check_for_pyzmq()
    check_for_readline()

def record_commit_info(pkg_dir, build_cmd=build_py):
    """ Return extended build command class for recording commit

    The extended command tries to run git to find the current commit, getting
    the empty string if it fails.  It then writes the commit hash into a file
    in the `pkg_dir` path, named ``.git_commit_info.ini``.

    In due course this information can be used by the package after it is
    installed, to tell you what commit it was installed from if known.

    To make use of this system, you need a package with a .git_commit_info.ini
    file - e.g. ``myproject/.git_commit_info.ini`` - that might well look like
    this::

        # This is an ini file that may contain information about the code state
        [commit hash]
        # The line below may contain a valid hash if it has been substituted
        # during 'git archive'
        archive_subst_hash=$Format:%h$
        # This line may be modified by the install process
        install_hash=

    The .git_commit_info file above is also designed to be used with git
    substitution - so you probably also want a ``.gitattributes`` file in the
    root directory of your working tree that contains something like this::

       myproject/.git_commit_info.ini export-subst

    That will cause the ``.git_commit_info.ini`` file to get filled in by ``git
    archive`` - useful in case someone makes such an archive - for example with
    via the github 'download source' button.

    Although all the above will work as is, you might consider having something
    like a ``get_info()`` function in your package to display the commit
    information at the terminal.  See the ``pkg_info.py`` module in the nipy
    package for an example.
    """
    class MyBuildPy(build_cmd):
        ''' Subclass to write commit data into installation tree '''
        def run(self):
            build_cmd.run(self)
            import subprocess
            proc = subprocess.Popen('git rev-parse --short HEAD',
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            repo_commit, _ = proc.communicate()
            # We write the installation commit even if it's empty
            cfg_parser = ConfigParser()
            cfg_parser.read(pjoin(pkg_dir, '.git_commit_info.ini'))
            if not cfg_parser.has_section('commit hash'):
                # just in case the ini file is empty or doesn't exist, somehow
                # we don't want the next line to raise
                cfg_parser.add_section('commit hash')
            cfg_parser.set('commit hash', 'install_hash', repo_commit.decode('ascii'))
            out_pth = pjoin(self.build_lib, pkg_dir, '.git_commit_info.ini')
            out_file = open(out_pth, 'wt')
            cfg_parser.write(out_file)
            out_file.close()
    return MyBuildPy
