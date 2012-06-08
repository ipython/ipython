# -*- coding: utf-8 -*-
"""
Tests for the virtualenvmagic extension
Author: Flávio Codeço Coelho - @fccoelho
"""

import os
import nose.tools as nt


def setup():
    ip = get_ipython()
    ip.extension_manager.load_extension('virtualenvmagic')
    
def test_virtualenv():
    ip = get_ipython()
    ip.run_cell_magic('virtualenv','pypyEnv','import sys')
    ip.ex('v = sys.version')
    nt.assert_true('PyPy' in ip.user_ns['v'])
