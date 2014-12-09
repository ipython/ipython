"""Base class for notebook tests."""

from __future__ import print_function

import sys
import time
import requests
from contextlib import contextmanager
from threading import Thread, Event
from unittest import TestCase

from tornado.ioloop import IOLoop

from ..notebookapp import NotebookApp
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
    config = None

    @classmethod
    def wait_until_alive(cls):
        """Wait for the server to be alive"""
        url = 'http://localhost:%i/api/contents' % cls.port
        for _ in range(int(MAX_WAITTIME/POLL_INTERVAL)):
            try:
                requests.get(url)
            except Exception as e:
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
        cls.notebook_thread.join(timeout=MAX_WAITTIME)
        if cls.notebook_thread.is_alive():
            raise TimeoutError("Undead notebook server")

    @classmethod
    def setup_class(cls):
        cls.ipython_dir = TemporaryDirectory()
        cls.notebook_dir = TemporaryDirectory()
        app = cls.notebook = NotebookApp(
            port=cls.port,
            port_retries=0,
            open_browser=False,
            ipython_dir=cls.ipython_dir.name,
            notebook_dir=cls.notebook_dir.name,
            config=cls.config,
        )
        
        # clear log handlers and propagate to root for nose to capture it
        # needs to be redone after initialize, which reconfigures logging
        app.log.propagate = True
        app.log.handlers = []
        app.initialize(argv=[])
        app.log.propagate = True
        app.log.handlers = []
        started = Event()
        def start_thread():
            loop = IOLoop.current()
            loop.add_callback(started.set)
            try:
                app.start()
            finally:
                # set the event, so failure to start doesn't cause a hang
                started.set()
        cls.notebook_thread = Thread(target=start_thread)
        cls.notebook_thread.start()
        started.wait()
        cls.wait_until_alive()

    @classmethod
    def teardown_class(cls):
        cls.notebook.stop()
        cls.wait_until_dead()
        cls.ipython_dir.cleanup()
        cls.notebook_dir.cleanup()

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
                    "Expected status %d, got %d" % (status, real_status)
        if msg:
            assert msg in str(e), e
    else:
        assert False, "Expected HTTP error status"