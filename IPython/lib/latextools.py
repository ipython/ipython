# -*- coding: utf-8 -*-
"""Tools for handling LaTeX.

Authors:

* Brian Granger
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2010, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from StringIO import StringIO
from base64 import encodestring

#-----------------------------------------------------------------------------
# Tools
#-----------------------------------------------------------------------------


def latex_to_png(s, encode=False):
    """Render a LaTeX string to PNG using matplotlib.mathtext.

    Parameters
    ----------
    s : str
        The raw string containing valid inline LaTeX.
    encode : bool, optional
        Should the PNG data bebase64 encoded to make it JSON'able.
    """
    from matplotlib import mathtext
    
    mt = mathtext.MathTextParser('bitmap')
    f = StringIO()
    mt.to_png(f, s, fontsize=12)
    bin_data = f.getvalue()
    if encode:
        bin_data = encodestring(bin_data)
    return bin_data

_data_uri_template_png = """<img src="data:image/png;base64,%s" alt=%s />"""

def latex_to_html(s, alt='image'):
    """Render LaTeX to HTML with embedded PNG data using data URIs.

    Parameters
    ----------
    s : str
        The raw string containing valid inline LateX.
    alt : str
        The alt text to use for the HTML.
    """
    base64_data = latex_to_png(s, encode=True)
    return _data_uri_template_png  % (base64_data, alt)

