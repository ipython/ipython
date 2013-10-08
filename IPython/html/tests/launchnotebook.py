"""Base class for notebook tests."""

import sys
import time
import requests
from contextlib import contextmanager
from subprocess import Popen, PIPE
from unittest import TestCase

from IPython.utils.tempdir import TemporaryDirectory

class NotebookTestBase(TestCase):
    """A base class for tests that need a running notebook.
    
    This creates an empty profile in a temp ipython_dir
    and then starts the notebook server with a separate temp notebook_dir.
    """

    port = 12341

    @classmethod
    def wait_until_alive(cls):
        """Wait for the server to be alive"""
        url = 'http://localhost:%i/api/notebooks' % cls.port
        while True:
            try:
                requests.get(url)
            except requests.exceptions.ConnectionError:
                time.sleep(.1)
            else:
                break
    
    @classmethod
    def wait_until_dead(cls):
        """Wait for the server to stop getting requests after shutdown"""
        url = 'http://localhost:%i/api/notebooks' % cls.port
        while True:
            try:
                requests.get(url)
            except requests.exceptions.ConnectionError:
                break
            else:
                time.sleep(.1)
    
    @classmethod
    def setup_class(cls):
        cls.ipython_dir = TemporaryDirectory()
        cls.notebook_dir = TemporaryDirectory()
        notebook_args = [
            sys.executable, '-c',
            'from IPython.html.notebookapp import launch_new_instance; launch_new_instance()',
            '--port=%d' % cls.port,
            '--no-browser',
            '--ipython-dir=%s' % cls.ipython_dir.name,
            '--notebook-dir=%s' % cls.notebook_dir.name
        ]        
        cls.notebook = Popen(notebook_args, stdout=PIPE, stderr=PIPE)
        cls.wait_until_alive()

    @classmethod
    def teardown_class(cls):
        cls.notebook.terminate()
        cls.ipython_dir.cleanup()
        cls.notebook_dir.cleanup()
        cls.wait_until_dead()

    @classmethod
    def base_url(cls):
        return 'http://localhost:%i/' % cls.port


@contextmanager
def assert_http_error(status):
    try:
        yield
    except requests.HTTPError as e:
        real_status = e.response.status_code
        assert real_status == status, \
                    "Expected status %d, got %d" % (real_status, status)
    else:
        assert False, "Expected HTTP error status"