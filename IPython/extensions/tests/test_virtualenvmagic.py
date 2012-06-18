# -*- coding: utf-8 -*-
"""
Tests for the virtualenvmagic extension
Author: Flávio Codeço Coelho - @fccoelho
"""

import nose.tools as nt
import os, shutil
from nose import SkipTest
import virtualenv
from IPython.utils.tempdir import TemporaryDirectory

home_dir = os.getenv('HOME')
user_venv_dir = os.path.join(home_dir,'Envs/') if not "WORKON_HOME" \
    in os.environ else os.getenv("WORKON_HOME")
if not os.path.exists(os.path.join(home_dir,'Envs/')):
    os.mkdir(os.path.join(home_dir,'Envs/'))

global testenv_dir



def setup():
    global testenv_dir
    ip = get_ipython()
    #creating a testing virtualenv
    testenv_dir = TemporaryDirectory()
    os.environ['WORKON_HOME'] = testenv_dir.name
    virtualenv.create_environment(os.path.join(testenv_dir.name,'testenv'))
    ip.extension_manager.load_extension('virtualenvmagic')

def teardown():
    del os.environ['WORKON_HOME']
    testenv_dir.cleanup()



def test_virtualenv_testenv():
    ip = get_ipython()
    result = ip.run_cell_magic('virtualenv', 'testenv', 'import sys;print(sys.path)')
    nt.assert_equals('tmp', os.path.split(eval(result)[1])[0].split(os.path.sep)[1])

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
    if os.path.exists(os.path.join(os.environ['WORKON_HOME'], env)):
        return True
    else:
        return False
