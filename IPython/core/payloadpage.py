# encoding: utf-8
"""
A payload based version of page.

Authors:

* Brian Granger
* Fernando Perez
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Third-party
try:
    from docutils.core import publish_string
except ImportError:
    # html paging won't be available, but we don't raise any errors.  It's a
    # purely optional feature.
    pass

# Our own
from IPython.core.interactiveshell import InteractiveShell

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

def page(strng, start=0, screen_lines=0, pager_cmd=None,
         html=None, auto_html=False):
    """Print a string, piping through a pager.

    This version ignores the screen_lines and pager_cmd arguments and uses
    IPython's payload system instead.

    Parameters
    ----------
    strng : str
      Text to page.

    start : int
      Starting line at which to place the display.
    
    html : str, optional
      If given, an html string to send as well.

    auto_html : bool, optional
      If true, the input string is assumed to be valid reStructuredText and is
      converted to HTML with docutils.  Note that if docutils is not found,
      this option is silently ignored.

    Notes
    -----

    Only one of the ``html`` and ``auto_html`` options can be given, not
    both.
    """

    # Some routines may auto-compute start offsets incorrectly and pass a
    # negative value.  Offset to 0 for robustness.
    start = max(0, start)
    shell = InteractiveShell.instance()

    if auto_html:
        try:
            # These defaults ensure user configuration variables for docutils
            # are not loaded, only our config is used here.
            defaults = {'file_insertion_enabled': 0,
                        'raw_enabled': 0,
                        '_disable_config': 1}
            html = publish_string(strng, writer_name='html',
                                  settings_overrides=defaults)
        except:
            pass
        
    payload = dict(
        source='page',
        text=strng,
        html=html,
        start_line_number=start
        )
    shell.payload_manager.write_payload(payload)


def install_payload_page():
    """Install this version of page as IPython.core.page.page."""
    from IPython.core import page as corepage
    corepage.page = page
