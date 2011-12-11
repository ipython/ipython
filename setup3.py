import os.path
import sys
from setuptools import setup
from setuptools.command.build_py import build_py

from setupbase import (setup_args,
                       find_scripts,
                       find_packages,
                       find_package_data,
                       record_commit_info,
                       )
    
setup_args['entry_points'] = find_scripts(True, suffix='3')
setup_args['packages'] = find_packages()
setup_args['package_data'] = find_package_data()
setup_args['cmdclass'] = {'build_py': record_commit_info('IPython', build_cmd=build_py)}

# Script to be run by the windows binary installer after the default setup
# routine, to add shortcuts and similar windows-only things.  Windows
# post-install scripts MUST reside in the scripts/ dir, otherwise distutils
# doesn't find them.
if 'bdist_wininst' in sys.argv:
    if len(sys.argv) > 2 and \
           ('sdist' in sys.argv or 'bdist_rpm' in sys.argv):
        print >> sys.stderr, "ERROR: bdist_wininst must be run alone. Exiting."
        sys.exit(1)
    setup_args['scripts'] = [os.path.join('scripts','ipython_win_post_install.py')]
    setup_args['options'] = {"bdist_wininst":
                             {"install_script":
                              "ipython_win_post_install.py"}}

def main():
    setup(use_2to3 = True, **setup_args)
    
if __name__ == "__main__":
    main()
