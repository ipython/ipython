import os.path
from setuptools import setup

from setupbase import (setup_args, find_scripts, find_packages)
    
setup_args['entry_points'] = find_scripts(True)
setup_args['packages'] = find_packages()

setup(use_2to3 = True, **setup_args)
