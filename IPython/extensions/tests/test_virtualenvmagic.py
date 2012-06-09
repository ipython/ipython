# -*- coding: utf-8 -*-
"""
Tests for the virtualenvmagic extension
Author: Flávio Codeço Coelho - @fccoelho
"""

import nose.tools as nt
import os
from nose import SkipTest


def setup():
    ip = get_ipython()
    ip.extension_manager.load_extension('virtualenvmagic')


def test_virtualenv_pypy():
    if not env_exists('pypyEnv'):
        raise SkipTest
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'pypyEnv', 'import sys;print\
     sys.version')
    nt.assert_true('PyPy' in result)

def test_virtualenv_python3():
    if not env_exists('py3'):
        raise SkipTest
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'py3', 'import sys;print \
    (sys.version_info.major)')
    nt.assert_equals('3\n', result)

@nt.nottest
def env_exists(env):
    """
    check if environment exists
    """
    if 'WORKON_HOME' not in os.environ:
        return False
    if os.path.exists(os.environ['WORKON_HOME'] + '/' + env):
        return True
    else:
        return False
