#!/usr/bin/env python
# encoding: utf-8
"""
The main IPython application object

Authors:

* Brian Granger
* Fernando Perez

Notes
-----
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.application import Application
from IPython.core import release
from IPython.core.iplib import InteractiveShell
from IPython.config.loader import IPythonArgParseConfigLoader

ipython_desc = """
A Python shell with automatic history (input and output), dynamic object
introspection, easier configuration, command completion, access to the system
shell and more.
"""

class IPythonAppCLConfigLoader(IPythonArgParseConfigLoader):
    arguments = (
        ()
    )

class IPythonApp(Application):
    name = 'ipython'
    config_file_name = 'ipython_config.py'

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPythonAppCLConfigLoader(
            description=ipython_desc,
            version=release.version)

    def construct(self):
        self.shell = InteractiveShell(
            name='__IP',
            parent=None,
            config=self.master_config
        )

    def start_app(self):
        self.shell.mainloop()


if __name__ == '__main__':
    app = IPythonApp()
    app.start()