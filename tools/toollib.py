"""Various utilities common to IPython release and maintenance tools.
"""
from __future__ import print_function

# Library imports
import os
import sys

from distutils.dir_util import remove_tree

# Useful shorthands
pjoin = os.path.join
cd = os.chdir

# Constants

# SSH root address of the archive site
archive_user = 'ipython@archive.ipython.org'
archive_dir = 'archive.ipython.org'
archive = '%s:%s' % (archive_user, archive_dir)

# Build commands
# Source dists
sdists = './setup.py sdist --formats=gztar,zip'
# Eggs
eggs = './setupegg.py bdist_egg'

# Windows builds.
# We do them separately, so that the extra Windows scripts don't get pulled
# into Unix builds (setup.py has code which checks for bdist_wininst).  Note
# that the install scripts args are added to the main distutils call in
# setup.py, so they don't need to be passed here.
#
# The Windows 64-bit installer can't be built by a Linux/Mac Python because ofa
# bug in distutils:  http://bugs.python.org/issue6792.
# So we have to build it with a wine-installed native Windows Python...
win_builds = ["python setup.py bdist_wininst",
              r"%s/.wine/dosdevices/c\:/Python27/python.exe setup.py build "
              "--plat-name=win-amd64 bdist_wininst "
              "--install-script=ipython_win_post_install.py" %
              os.environ['HOME'] ]

# Utility functions
def sh(cmd):
    """Run system command in shell, raise SystemExit if it returns an error."""
    print("$", cmd)
    stat = os.system(cmd)
    #stat = 0  # Uncomment this and comment previous to run in debug mode
    if stat:
        raise SystemExit("Command %s failed with code: %s" % (cmd, stat))

# Backwards compatibility
c = sh

def get_ipdir():
    """Get IPython directory from command line, or assume it's the one above."""

    # Initialize arguments and check location
    try:
        ipdir = sys.argv[1]
    except IndexError:
        ipdir = '..'

    ipdir = os.path.abspath(ipdir)

    cd(ipdir)
    if not os.path.isdir('IPython') and os.path.isfile('setup.py'):
        raise SystemExit('Invalid ipython directory: %s' % ipdir)
    return ipdir


def compile_tree():
    """Compile all Python files below current directory."""
    stat = os.system('python -m compileall .')
    if stat:
        msg = '*** ERROR: Some Python files in tree do NOT compile! ***\n'
        msg += 'See messages above for the actual file that produced it.\n'
        raise SystemExit(msg)
