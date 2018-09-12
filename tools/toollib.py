"""Various utilities common to IPython release and maintenance tools.
"""

# Library imports
import os
import sys

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
sdists = './setup.py sdist --formats=gztar'
# Binary dists
def buildwheels():
    sh('{python} setupegg.py bdist_wheel'.format(python=sys.executable))

# Utility functions
def sh(cmd):
    """Run system command in shell, raise SystemExit if it returns an error."""
    print("$", cmd)
    stat = os.system(cmd)
    #stat = 0  # Uncomment this and comment previous to run in debug mode
    if stat:
        raise SystemExit("Command %s failed with code: %s" % (cmd, stat))

def get_ipdir():
    """Get IPython directory from command line, or assume it's the one above."""

    # Initialize arguments and check location
    ipdir = pjoin(os.path.dirname(__file__), os.pardir)

    ipdir = os.path.abspath(ipdir)

    cd(ipdir)
    if not os.path.isdir('IPython') and os.path.isfile('setup.py'):
        raise SystemExit('Invalid ipython directory: %s' % ipdir)
    return ipdir

def execfile(fname, globs, locs=None):
    locs = locs or globs
    exec(compile(open(fname).read(), fname, "exec"), globs, locs)
