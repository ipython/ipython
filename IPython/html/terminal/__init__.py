import os
from terminado import NamedTermManager
from .handlers import TerminalHandler, NewTerminalHandler, TermSocket

def initialize(webapp):
    shell = os.environ.get('SHELL', 'sh')
    webapp.terminal_manager = NamedTermManager(shell_command=[shell])
    handlers = [
        (r"/terminals/new", NewTerminalHandler),
        (r"/terminals/(\w+)", TerminalHandler),
        (r"/terminals/websocket/(\w+)", TermSocket,
             {'term_manager': webapp.terminal_manager}),
    ]
    webapp.add_handlers(".*$", handlers)