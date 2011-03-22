"""Tests for IPython.core.application"""

import os
import tempfile

from IPython.core.application import Application

def test_unicode_cwd():
    """Check that IPython can start with unicode characters in the path."""
    wd = tempfile.mkdtemp(suffix="€")
    
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
