"""A print function that pretty prints sympy Basic objects.

Authors:
* Brian Granger
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

from sympy import pretty

#-----------------------------------------------------------------------------
# Definitions of magic functions for use with IPython
#-----------------------------------------------------------------------------

def print_basic_unicode(o, p, cycle):
    """A function to pretty print sympy Basic objects."""
    if cycle:
        return p.text('Basic(...)')
    out = pretty(o, use_unicode=True)
    if '\n' in out:
        p.text(u'\n')
    p.text(out)


_loaded = False


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plaintext_formatter = ip.display_formatter.formatters['text/plain']
        plaintext_formatter.for_type_by_name(
            'sympy.core.basic', 'Basic', print_basic_unicode
        )
        _loaded = True

