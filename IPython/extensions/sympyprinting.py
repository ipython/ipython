"""
A print function that pretty prints sympy Basic objects.

:moduleauthor: Brian Granger

Usage
=====

Once the extension is loaded, Sympy Basic objects are automatically
pretty-printed.

As of SymPy 0.7.2, maintenance of this extension has moved to SymPy under
sympy.interactive.ipythonprinting, any modifications to account for changes to
SymPy should be submitted to SymPy rather than changed here. This module is
maintained here for backwards compatablitiy with old SymPy versions.

"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
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

import warnings

#-----------------------------------------------------------------------------
# Definitions of special display functions for use with IPython
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
    """
    A function to display sympy expression using inline style LaTeX in PNG.
    """
    s = latex(o, mode='inline')
    # mathtext does not understand certain latex flags, so we try to replace
    # them with suitable subs.
    s = s.replace('\\operatorname','')
    s = s.replace('\\overline', '\\bar')
    png = latex_to_png(s)
    return png


def print_display_png(o):
    """
    A function to display sympy expression using display style LaTeX in PNG.
    """
    s = latex(o, mode='plain')
    s = s.strip('$')
    # As matplotlib does not support display style, dvipng backend is
    # used here.
    png = latex_to_png(s, backend='dvipng', wrap=True)
    return png


def can_print_latex(o):
    """
    Return True if type o can be printed with LaTeX.

    If o is a container type, this is True if and only if every element of o
    can be printed with LaTeX.
    """
    import sympy
    if isinstance(o, (list, tuple, set, frozenset)):
        return all(can_print_latex(i) for i in o)
    elif isinstance(o, dict):
        return all((isinstance(i, basestring) or can_print_latex(i)) and can_print_latex(o[i]) for i in o)
    elif isinstance(o,(sympy.Basic, sympy.matrices.Matrix, int, long, float)):
        return True
    return False

def print_latex(o):
    """A function to generate the latex representation of sympy
    expressions."""
    if can_print_latex(o):
        s = latex(o, mode='plain')
        s = s.replace('\\dag','\\dagger')
        s = s.strip('$')
        return '$$%s$$' % s
    # Fallback to the string printer
    return None

_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    import sympy

    # sympyprinting extension has been moved to SymPy as of 0.7.2, if it
    # exists there, warn the user and import it
    try:
        import sympy.interactive.ipythonprinting
    except ImportError:
        pass
    else:
        warnings.warn("The sympyprinting extension in IPython is deprecated, "
            "use sympy.interactive.ipythonprinting")
        ip.extension_manager.load_extension('sympy.interactive.ipythonprinting')
        return

    global _loaded
    if not _loaded:
        plaintext_formatter = ip.display_formatter.formatters['text/plain']

        for cls in (object, str):
            plaintext_formatter.for_type(cls, print_basic_unicode)

        printable_containers = [list, tuple]

        # set and frozen set were broken with SymPy's latex() function, but
        # was fixed in the 0.7.1-git development version. See
        # http://code.google.com/p/sympy/issues/detail?id=3062.
        if sympy.__version__ > '0.7.1':
            printable_containers += [set, frozenset]
        else:
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
        png_formatter.for_type_by_name(
            'sympy.matrices.matrices', 'Matrix', print_display_png
        )
        for cls in [dict, int, long, float] + printable_containers:
            png_formatter.for_type(cls, print_png)

        latex_formatter = ip.display_formatter.formatters['text/latex']
        latex_formatter.for_type_by_name(
            'sympy.core.basic', 'Basic', print_latex
        )
        latex_formatter.for_type_by_name(
            'sympy.matrices.matrices', 'Matrix', print_latex
        )

        for cls in printable_containers:
            # Use LaTeX only if every element is printable by latex
            latex_formatter.for_type(cls, print_latex)

        _loaded = True
