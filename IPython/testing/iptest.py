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

    argv = sys.argv + [ '--with-ipdoctest',
                        '--doctest-tests','--doctest-extension=txt',
                        '--detailed-errors',
                       
                        # We add --exe because of setuptools' imbecility (it
                        # blindly does chmod +x on ALL files).  Nose does the
                        # right thing and it tries to avoid executables,
                        # setuptools unfortunately forces our hand here.  This
                        # has been discussed on the distutils list and the
                        # setuptools devs refuse to fix this problem!
                        '--exe',
                        ]

    # Detect if any tests were required by explicitly calling an IPython
    # submodule or giving a specific path
    has_tests = False
    for arg in sys.argv:
        if 'IPython' in arg or arg.endswith('.py') or \
           (':' in arg and  '.py' in arg):
            has_tests = True
            break
    # If nothing was specifically requested, test full IPython
    if not has_tests:
        argv.append('IPython')

    # construct list of plugins, omitting the existing doctest plugin
    plugins = [IPythonDoctest()]
    for p in nose.plugins.builtin.plugins:
        plug = p()
        if plug.name == 'doctest':
            continue

        #print '*** adding plugin:',plug.name  # dbg
        plugins.append(plug)

    TestProgram(argv=argv,plugins=plugins)
