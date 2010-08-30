"""Various utilities common to IPython release and maintenance tools.
"""
# Library imports
import os
import sys

from distutils.dir_util import remove_tree

# Useful shorthands
pjoin = os.path.join
cd = os.chdir

# Utility functions
def c(cmd):
    """Run system command, raise SystemExit if it returns an error."""
    print "$",cmd
    stat = os.system(cmd)
    #stat = 0  # Uncomment this and comment previous to run in debug mode
    if stat:
        raise SystemExit("Command %s failed with code: %s" % (cmd, stat))


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
    vstr = '.'.join(map(str,sys.version_info[:2]))
    stat = os.system('python %s/lib/python%s/compileall.py .' %
                     (sys.prefix,vstr))
    if stat:
        msg = '*** ERROR: Some Python files in tree do NOT compile! ***\n'
        msg += 'See messages above for the actual file that produced it.\n'
        raise SystemExit(msg)
