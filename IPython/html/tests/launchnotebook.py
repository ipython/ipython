"""Base class for notebook tests."""

from __future__ import print_function

import sys
import time
import requests
from contextlib import contextmanager
from subprocess import Popen, STDOUT
from unittest import TestCase

import nose

from IPython.utils.tempdir import TemporaryDirectory

MAX_WAITTIME = 30   # seconds to wait for notebook server to start
POLL_INTERVAL = 0.1 # time between attempts

# TimeoutError is a builtin on Python 3. This can be removed when we stop
# supporting Python 2.
class TimeoutError(Exception):
    pass

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
        for _ in range(int(MAX_WAITTIME/POLL_INTERVAL)):
            try:
                requests.get(url)
            except requests.exceptions.ConnectionError:
                if cls.notebook.poll() is not None:
                    raise RuntimeError("The notebook server exited with status %s" \
                                        % cls.notebook.poll())
                time.sleep(POLL_INTERVAL)
            else:
                return

        raise TimeoutError("The notebook server didn't start up correctly.")
    
    @classmethod
    def wait_until_dead(cls):
        """Wait for the server process to terminate after shutdown"""
        for _ in range(int(MAX_WAITTIME/POLL_INTERVAL)):
            if cls.notebook.poll() is not None:
                return
            time.sleep(POLL_INTERVAL)
    
        raise TimeoutError("Undead notebook server")

    @classmethod
    def setup_class(cls):
        cls.ipython_dir = TemporaryDirectory()
        cls.notebook_dir = TemporaryDirectory()
        notebook_args = [
            sys.executable, '-c',
            'from IPython.html.notebookapp import launch_new_instance; launch_new_instance()',
            '--port=%d' % cls.port,
            '--port-retries=0',  # Don't try any other ports
            '--no-browser',
            '--ipython-dir=%s' % cls.ipython_dir.name,
            '--notebook-dir=%s' % cls.notebook_dir.name,
        ]
        cls.notebook = Popen(notebook_args,
            stdout=nose.iptest_stdstreams_fileno(),
            stderr=STDOUT,
        )
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
def assert_http_error(status, msg=None):
    try:
        yield
    except requests.HTTPError as e:
        real_status = e.response.status_code
        assert real_status == status, \
                    "Expected status %d, got %d" % (real_status, status)
        if msg:
            assert msg in str(e), e
    else:
        assert False, "Expected HTTP error status"