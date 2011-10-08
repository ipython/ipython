"""
A print function that pretty prints sympy Basic objects.

:moduleauthor: Brian Granger

Usage
=====

Once the extension is loaded, Sympy Basic objects are automatically
pretty-printed.

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

from IPython.lib.latextools import latex_to_png
from IPython.testing import decorators as dec
# use @dec.skipif_not_sympy to skip tests requiring sympy

try:
    from sympy import pretty, latex
except ImportError:
    pass


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


def print_png(o):
    """A function to display sympy expression using LaTex -> PNG."""
    s = latex(o, mode='inline')
    # mathtext does not understand certain latex flags, so we try to replace
    # them with suitable subs.
    s = s.replace('\\operatorname','')
    s = s.replace('\\overline', '\\bar')
    png = latex_to_png(s)
    return png


def print_latex(o):
    """A function to generate the latex representation of sympy expressions."""
    s = latex(o, mode='equation', itex=True)
    s = s.replace('\\dag','\\dagger')
    return s


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plaintext_formatter = ip.display_formatter.formatters['text/plain']

        for cls in (object, tuple, list, set, frozenset, dict, str):
            plaintext_formatter.for_type(cls, print_basic_unicode)

        plaintext_formatter.for_type_by_name(
            'sympy.core.basic', 'Basic', print_basic_unicode
        )
        plaintext_formatter.for_type_by_name(
            'sympy.matrices.matrices', 'Matrix', print_basic_unicode
        )

        png_formatter = ip.display_formatter.formatters['image/png']

        png_formatter.for_type_by_name(
            'sympy.core.basic', 'Basic', print_png
        )

        latex_formatter = ip.display_formatter.formatters['text/latex']
        latex_formatter.for_type_by_name(
            'sympy.core.basic', 'Basic', print_latex
        )
        latex_formatter.for_type_by_name(
            'sympy.matrices.matrices', 'Matrix', print_latex
        )
        _loaded = True

