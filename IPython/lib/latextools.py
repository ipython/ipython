# -*- coding: utf-8 -*-
"""Tools for handling LaTeX.

Authors:

* Brian Granger
"""
#-----------------------------------------------------------------------------
# Copyright (C) 2010 IPython Development Team.
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
import os
import tempfile
import shutil
import subprocess

from IPython.utils.process import find_cmd, FindCmdError

#-----------------------------------------------------------------------------
# Tools
#-----------------------------------------------------------------------------


def latex_to_png(s, encode=False, backend='mpl'):
    """Render a LaTeX string to PNG.

    Parameters
    ----------
    s : str
        The raw string containing valid inline LaTeX.
    encode : bool, optional
        Should the PNG data bebase64 encoded to make it JSON'able.
    backend : {mpl, dvipng}
        Backend for producing PNG data.

    None is returned when the backend cannot be used.

    """
    if backend == 'mpl':
        f = latex_to_png_mpl
    elif backend == 'dvipng':
        f = latex_to_png_dvipng
    else:
        raise ValueError('No such backend {0}'.format(backend))
    bin_data = f(s)
    if encode and bin_data:
        bin_data = encodestring(bin_data)
    return bin_data


def latex_to_png_mpl(s):
    try:
        from matplotlib import mathtext
    except ImportError:
        return None
    
    mt = mathtext.MathTextParser('bitmap')
    f = StringIO()
    mt.to_png(f, s, fontsize=12)
    return f.getvalue()


def latex_to_png_dvipng(s):
    try:
        find_cmd('latex')
        find_cmd('dvipng')
    except FindCmdError:
        return None
    try:
        workdir = tempfile.mkdtemp()
        tmpfile = os.path.join(workdir, "tmp.tex")
        dvifile = os.path.join(workdir, "tmp.dvi")
        outfile = os.path.join(workdir, "tmp.png")

        with open(tmpfile, "w") as f:
            f.write(_latex_header)
            f.write(s)
            f.write(_latex_footer)

        subprocess.check_call(
            ["latex", "-halt-on-errror", tmpfile], cwd=workdir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        subprocess.check_call(
            ["dvipng", "-T", "tight", "-x", "1500", "-z", "9",
             "-bg", "transparent", "-o", outfile, dvifile], cwd=workdir,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(outfile) as f:
            bin_data = f.read()
    finally:
        shutil.rmtree(workdir)
    return bin_data


_latex_header = r'''
\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
'''

_latex_footer = r'\end{document}'


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
    if base64_data:
        return _data_uri_template_png  % (base64_data, alt)


# From matplotlib, thanks to mdboom. Once this is in matplotlib releases, we
# will remove.
def math_to_image(s, filename_or_obj, prop=None, dpi=None, format=None):
    """
    Given a math expression, renders it in a closely-clipped bounding
    box to an image file.

    *s*
       A math expression.  The math portion should be enclosed in
       dollar signs.

    *filename_or_obj*
       A filepath or writable file-like object to write the image data
       to.

    *prop*
       If provided, a FontProperties() object describing the size and
       style of the text.

    *dpi*
       Override the output dpi, otherwise use the default associated
       with the output format.

    *format*
       The output format, eg. 'svg', 'pdf', 'ps' or 'png'.  If not
       provided, will be deduced from the filename.
    """
    from matplotlib import figure
    # backend_agg supports all of the core output formats
    from matplotlib.backends import backend_agg
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import MathTextParser

    if prop is None:
        prop = FontProperties()

    parser = MathTextParser('path')
    width, height, depth, _, _ = parser.parse(s, dpi=72, prop=prop)

    fig = figure.Figure(figsize=(width / 72.0, height / 72.0))
    fig.text(0, depth/height, s, fontproperties=prop)
    backend_agg.FigureCanvasAgg(fig)
    fig.savefig(filename_or_obj, dpi=dpi, format=format)

    return depth

