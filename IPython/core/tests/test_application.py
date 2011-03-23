# coding: utf-8
"""Tests for IPython.core.application"""

import os
import tempfile

from IPython.core.application import Application

def test_unicode_cwd():
    """Check that IPython starts with non-ascii characters in the path."""
    wd = tempfile.mkdtemp(suffix=u"€")
    
    old_wd = os.getcwdu()
    os.chdir(wd)
    #raise Exception(repr(os.getcwd()))
    try:
        app = Application()
        # The lines below are copied from Application.initialize()
        app.create_default_config()
        app.log_default_config()
        app.set_default_config_log_level()

        # Find resources needed for filesystem access, using information from
        # the above two
        app.find_ipython_dir()
        app.find_resources()
        app.find_config_file_name()
        app.find_config_file_paths()

        # File-based config
        app.pre_load_file_config()
        app.load_file_config(suppress_errors=False)
    finally:
        os.chdir(old_wd)
        
def test_unicode_ipdir():
    """Check that IPython starts with non-ascii characters in the IP dir."""
    ipdir = tempfile.mkdtemp(suffix=u"€")
    
    # Create the config file, so it tries to load it.
    with open(os.path.join(ipdir, 'ipython_config.py'), "w") as f:
        pass
    
    old_ipdir1 = os.environ.pop("IPYTHONDIR", None)
    old_ipdir2 = os.environ.pop("IPYTHON_DIR", None)
    os.environ["IPYTHONDIR"] = ipdir.encode("utf-8")
    try:
        app = Application()
        # The lines below are copied from Application.initialize()
        app.create_default_config()
        app.log_default_config()
        app.set_default_config_log_level()

        # Find resources needed for filesystem access, using information from
        # the above two
        app.find_ipython_dir()
        app.find_resources()
        app.find_config_file_name()
        app.find_config_file_paths()

        # File-based config
        app.pre_load_file_config()
        app.load_file_config(suppress_errors=False)
    finally:
        if old_ipdir1:
            os.environ["IPYTHONDIR"] = old_ipdir1
        if old_ipdir2:
            os.environ["IPYTHONDIR"] = old_ipdir2
