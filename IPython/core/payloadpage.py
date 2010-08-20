#!/usr/bin/env python
# encoding: utf-8
"""
A payload based version of page.

Authors:

* Brian Granger
* Fernando Perez
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.interactiveshell import InteractiveShell

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def page(strng, start=0, screen_lines=0, pager_cmd=None):
    """Print a string, piping through a pager.

    This version ignores the screen_lines and pager_cmd arguments and uses
    IPython's payload system instead.
    """

    # Some routines may auto-compute start offsets incorrectly and pass a
    # negative value.  Offset to 0 for robustness.
    start = max(0, start)
    shell = InteractiveShell.instance()
    payload = dict(
        source='IPython.zmq.page.page',
        data=strng,
        start_line_number=start
    )
    shell.payload_manager.write_payload(payload)

def install_payload_page():
    """Install this version of page as IPython.core.page.page."""
    from IPython.core import page as corepage
    corepage.page = page
