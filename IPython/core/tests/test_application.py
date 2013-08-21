# coding: utf-8
"""Tests for IPython.core.application"""

import os
import tempfile
import shutil

import nose.tools as nt

from IPython.core.application import BaseIPythonApplication
from IPython.testing import decorators as dec
from IPython.testing.tools import make_tempfile, ipexec
from IPython.utils import py3compat

@dec.onlyif_unicode_paths
def test_unicode_cwd():
    """Check that IPython starts with non-ascii characters in the path."""
    wd = tempfile.mkdtemp(suffix=u"€")
    
    old_wd = os.getcwdu()
    os.chdir(wd)
    #raise Exception(repr(os.getcwdu()))
    try:
        app = BaseIPythonApplication()
        # The lines below are copied from Application.initialize()
        app.init_profile_dir()
        app.init_config_files()
        app.load_config_file(suppress_errors=False)
    finally:
        os.chdir(old_wd)

@dec.onlyif_unicode_paths
def test_unicode_ipdir():
    """Check that IPython starts with non-ascii characters in the IP dir."""
    ipdir = tempfile.mkdtemp(suffix=u"€")
    
    # Create the config file, so it tries to load it.
    with open(os.path.join(ipdir, 'ipython_config.py'), "w") as f:
        pass
    
    old_ipdir1 = os.environ.pop("IPYTHONDIR", None)
    old_ipdir2 = os.environ.pop("IPYTHON_DIR", None)
    os.environ["IPYTHONDIR"] = py3compat.unicode_to_str(ipdir, "utf-8")
    try:
        app = BaseIPythonApplication()
        # The lines below are copied from Application.initialize()
        app.init_profile_dir()
        app.init_config_files()
        app.load_config_file(suppress_errors=False)
    finally:
        if old_ipdir1:
            os.environ["IPYTHONDIR"] = old_ipdir1
        if old_ipdir2:
            os.environ["IPYTHONDIR"] = old_ipdir2



TEST_SYNTAX_ERROR_CMDS = """
from IPython.core.inputtransformer import InputTransformer

%cpaste
class SyntaxErrorTransformer(InputTransformer):

    def push(self, line):
        if 'syntaxerror' in line:
            raise SyntaxError('in input '+line)
        return line

    def reset(self):
        pass
--

ip = get_ipython()
transformer = SyntaxErrorTransformer()
ip.input_splitter.python_line_transforms.append(transformer)
ip.input_transformer_manager.python_line_transforms.append(transformer)

# now the actual commands
1234
2345  # syntaxerror <- triggered here
3456
"""

def test_syntax_error():
    """Check that IPython does not abort if a SyntaxError is raised in an InputTransformer"""
    try:
        tmp = tempfile.mkdtemp()
        filename = os.path.join(tmp, 'test_syntax_error.py')
        with open(filename, 'w') as f:
            f.write(TEST_SYNTAX_ERROR_CMDS)
        out, err = ipexec(filename, pipe=True)
        nt.assert_equal(err, '')
        nt.assert_in('1234', out)
        nt.assert_in('SyntaxError: in input 2345  # syntaxerror <- triggered here', out)
        nt.assert_in('3456', out)
    finally:
        shutil.rmtree(tmp)
