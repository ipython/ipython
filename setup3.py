import os.path
import sys
from setuptools import setup
from setuptools.command.build_py import build_py

from setupbase import (setup_args,
                       find_scripts,
                       find_packages,
                       find_package_data,
                       record_commit_info,
                       bdist_wininst_options,
                       )
    
setup_args['entry_points'] = find_scripts(True, suffix='3')
setup_args['packages'] = find_packages()
setup_args['package_data'] = find_package_data()
setup_args['cmdclass'] = {'build_py': 
                          record_commit_info('IPython', build_cmd=build_py)}

setup_args.update(bdist_wininst_options())

def main():
    setup(use_2to3 = True, **setup_args)
    
if __name__ == "__main__":
    main()
