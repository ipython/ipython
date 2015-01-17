import os

import terminado
from IPython.utils.version import check_version

if not check_version(terminado.__version__, '0.3.3'):
    raise ImportError("terminado >= 0.3.3 required, found %s" % terminado.__version__)

from terminado import NamedTermManager
from tornado.log import app_log
from IPython.html.utils import url_path_join as ujoin
from .handlers import TerminalHandler, TermSocket
from . import api_handlers

def initialize(webapp):
    shell = os.environ.get('SHELL', 'sh')
    terminal_manager = webapp.settings['terminal_manager'] = NamedTermManager(shell_command=[shell])
    terminal_manager.log = app_log
    base_url = webapp.settings['base_url']
    handlers = [
        (ujoin(base_url, r"/terminals/(\w+)"), TerminalHandler),
        (ujoin(base_url, r"/terminals/websocket/(\w+)"), TermSocket,
             {'term_manager': terminal_manager}),
        (ujoin(base_url, r"/api/terminals"), api_handlers.TerminalRootHandler),
        (ujoin(base_url, r"/api/terminals/(\w+)"), api_handlers.TerminalHandler),
    ]
    webapp.add_handlers(".*$", handlers)