#!/usr/bin/env python
"""
A minimal front end to the Docutils Publisher, producing an ipython notebook.
"""

import docutils.readers.standalone
import docutils.parsers.rst
import docutils.core
import rst2ipynblib
from docutils.core import publish_cmdline

description = ('Generates an ipython notebook from standalone '
               'reStructuredText source. ' +
               docutils.core.default_description)

publish_cmdline(reader=docutils.readers.standalone.Reader(),
                          parser=docutils.parsers.rst.Parser(),
                          writer=rst2ipynblib.Writer(),
                          enable_exit_status=1,
                          usage=docutils.core.default_usage,
                          description=description)
