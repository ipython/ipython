# -*- coding: utf-8 -*-
"""
Tests for the virtualenvmagic extension
Author: Flávio Codeço Coelho - @fccoelho
"""

import nose.tools as nt
import os, shutil
from nose import SkipTest
import virtualenv

home_dir = os.getenv('HOME')
venv_dir = os.path.join(home_dir,'Envs/') if not "WORKON_HOME" \
    in os.environ else os.getenv("WORKON_HOME")
if not os.path.exists(os.path.join(home_dir,'Envs/')):
    os.mkdir(os.path.join(home_dir,'Envs/'))

testenv_dir = os.path.join(venv_dir,'testenv')
if not os.path.exists(os.path.join(venv_dir,'testenv')):
    os.mkdir(os.path.join(venv_dir,'testenv'))



def setup():
    ip = get_ipython()
    #creating a testing virtual
    virtualenv.create_environment(testenv_dir)
    ip.extension_manager.load_extension('virtualenvmagic')

def teardown():
    shutil.rmtree(testenv_dir)


def test_virtualenv_pypy():
    if not env_exists('pypyEnv'):
        raise SkipTest("Environment pypyEnv not found, skipping test")
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'pypyEnv', 'import sys;print\
     (sys.version)')
    nt.assert_true('PyPy' in result)

def test_virtualenv_python3():
    if not env_exists('py3'):
        raise SkipTest("Environment py3 not found, skipping test")
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'py3', 'import sys;print \
    (sys.version_info.major)')
    nt.assert_equals('3\n', result)

def test_virtualenv_testenv():
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'testenv', 'print("hello")')
    nt.assert_equals('hello\n', result)

def test_virtualenv_nonexisting():
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'nonexistingenv', 'print("hello")')
    nt.assert_equals(None, result)

def test_capturing_python_error():
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'testenv', 'print(x)')
    # traceback is sent to stderror
    nt.assert_equals("",result)

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
