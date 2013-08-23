"""Base class for notebook tests."""

import sys
import time
import requests
from subprocess import Popen, PIPE
from unittest import TestCase

from IPython.utils.tempdir import TemporaryDirectory


class NotebookTestBase(TestCase):
    """A base class for tests that need a running notebook.
    
    This creates an empty profile in a temp ipython_dir
    and then starts the notebook server with a separate temp notebook_dir.
    """

    port = 1234

    def wait_till_alive(self):
        url = 'http://localhost:%i/' % self.port
        while True:
            time.sleep(.1)
            try:
                r = requests.get(url + 'api/notebooks')
                break
            except requests.exceptions.ConnectionError:
                pass
        
    def wait_till_dead(self):
        url = 'http://localhost:%i/' % self.port
        while True:
            time.sleep(.1)
            try:
                r = requests.get(url + 'api/notebooks')
                continue
            except requests.exceptions.ConnectionError:
                break

    def setUp(self):
        self.ipython_dir = TemporaryDirectory()
        self.notebook_dir = TemporaryDirectory()
        notebook_args = [
            sys.executable, '-c',
            'from IPython.html.notebookapp import launch_new_instance; launch_new_instance()',
            '--port=%d' % self.port,
            '--no-browser',
            '--ipython-dir=%s' % self.ipython_dir.name,
            '--notebook-dir=%s' % self.notebook_dir.name
        ]  
        self.notebook = Popen(notebook_args, stdout=PIPE, stderr=PIPE)
        self.wait_till_alive()
        #time.sleep(3.0)

    def tearDown(self):
        self.notebook.terminate()
        self.ipython_dir.cleanup()
        self.notebook_dir.cleanup()
        self.wait_till_dead()
        
    def base_url(self):
        return 'http://localhost:%i/' % self.port
