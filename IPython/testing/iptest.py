#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPython Test Suite Runner.
"""

import sys
import warnings

from nose.core import TestProgram
import nose.plugins.builtin

from IPython.testing.plugin.ipdoctest import IPythonDoctest

def main():
    """Run the IPython test suite.
    """

    warnings.filterwarnings('ignore', 
        'This will be removed soon.  Use IPython.testing.util instead')

    
    # construct list of plugins, omitting the existing doctest plugin
    plugins = [IPythonDoctest()]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue

        #print 'adding plugin:',plug.name  # dbg
        plugins.append(plug)

    argv = sys.argv + ['--doctest-tests','--doctest-extension=txt',
                       '--detailed-errors',
                       
                       # We add --exe because of setuptools' imbecility (it
                       # blindly does chmod +x on ALL files).  Nose does the
                       # right thing and it tries to avoid executables,
                       # setuptools unfortunately forces our hand here.  This
                       # has been discussed on the distutils list and the
                       # setuptools devs refuse to fix this problem!
                       '--exe',
                       ]

    has_ip = False
    for arg in sys.argv:
        if 'IPython' in arg:
            has_ip = True
            break

    if not has_ip:
        argv.append('IPython')

    TestProgram(argv=argv,plugins=plugins)
