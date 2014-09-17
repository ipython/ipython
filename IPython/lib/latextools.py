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

from io import BytesIO
from base64 import encodestring
import os
import tempfile
import shutil
import subprocess

from IPython.utils.process import find_cmd, FindCmdError
from IPython.config.configurable import SingletonConfigurable
from IPython.utils.traitlets import List, CBool, CUnicode
from IPython.utils.py3compat import bytes_to_str

#-----------------------------------------------------------------------------
# Tools
#-----------------------------------------------------------------------------


class LaTeXTool(SingletonConfigurable):
    """An object to store configuration of the LaTeX tool."""

    backends = List(
        CUnicode, ["matplotlib", "dvipng"],
        help="Preferred backend to draw LaTeX math equations. "
        "Backends in the list are checked one by one and the first "
        "usable one is used.  Note that `matplotlib` backend "
        "is usable only for inline style equations.  To draw  "
        "display style equations, `dvipng` backend must be specified. ",
        # It is a List instead of Enum, to make configuration more
        # flexible.  For example, to use matplotlib mainly but dvipng
        # for display style, the default ["matplotlib", "dvipng"] can
        # be used.  To NOT use dvipng so that other repr such as
        # unicode pretty printing is used, you can use ["matplotlib"].
        config=True)

    use_breqn = CBool(
        True,
        help="Use breqn.sty to automatically break long equations. "
        "This configuration takes effect only for dvipng backend.",
        config=True)

    packages = List(
        ['amsmath', 'amsthm', 'amssymb', 'bm'],
        help="A list of packages to use for dvipng backend. "
        "'breqn' will be automatically appended when use_breqn=True.",
        config=True)

    preamble = CUnicode(
        help="Additional preamble to use when generating LaTeX source "
        "for dvipng backend.",
        config=True)


def latex_to_png(s, encode=False, backend=None, wrap=False):
    """Render a LaTeX string to PNG.

    Parameters
    ----------
    s : str
        The raw string containing valid inline LaTeX.
    encode : bool, optional
        Should the PNG data bebase64 encoded to make it JSON'able.
    backend : {matplotlib, dvipng}
        Backend for producing PNG data.
    wrap : bool
        If true, Automatically wrap `s` as a LaTeX equation.

    None is returned when the backend cannot be used.

    """
    allowed_backends = LaTeXTool.instance().backends
    if backend is None:
        backend = allowed_backends[0]
    if backend not in allowed_backends:
        return None
    if backend == 'matplotlib':
        f = latex_to_png_mpl
    elif backend == 'dvipng':
        f = latex_to_png_dvipng
    else:
        raise ValueError('No such backend {0}'.format(backend))
    bin_data = f(s, wrap)
    if encode and bin_data:
        bin_data = encodestring(bin_data)
    return bin_data


def latex_to_png_mpl(s, wrap):
    try:
        from matplotlib import mathtext
    except ImportError:
        return None

    if wrap:
        s = '${0}$'.format(s)
    mt = mathtext.MathTextParser('bitmap')
    f = BytesIO()
    mt.to_png(f, s, fontsize=12)
    return f.getvalue()


def latex_to_png_dvipng(s, wrap):
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
            f.writelines(genelatex(s, wrap))

        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(
                ["latex", "-halt-on-error", "-interaction", "batchmode", tmpfile],
                cwd=workdir, stdout=devnull, stderr=devnull)

            subprocess.check_call(
                ["dvipng", "-T", "tight", "-x", "1500", "-z", "9",
                 "-bg", "transparent", "-o", outfile, dvifile], cwd=workdir,
                stdout=devnull, stderr=devnull)

        with open(outfile, "rb") as f:
            return f.read()
    finally:
        shutil.rmtree(workdir)


def kpsewhich(filename):
    """Invoke kpsewhich command with an argument `filename`."""
    try:
        find_cmd("kpsewhich")
        proc = subprocess.Popen(
            ["kpsewhich", filename],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        return stdout.strip()
    except FindCmdError:
        pass


def genelatex(body, wrap):
    """Generate LaTeX document for dvipng backend."""
    lt = LaTeXTool.instance()
    breqn = wrap and lt.use_breqn and kpsewhich("breqn.sty")
    yield r'\documentclass{article}'
    packages = lt.packages
    if breqn:
        packages = packages + ['breqn']
    for pack in packages:
        yield r'\usepackage{{{0}}}'.format(pack)
    yield r'\pagestyle{empty}'
    if lt.preamble:
        yield lt.preamble
    yield r'\begin{document}'
    if breqn:
        yield r'\begin{dmath*}'
        yield body
        yield r'\end{dmath*}'
    elif wrap:
        yield '$${0}$$'.format(body)
    else:
        yield body
    yield r'\end{document}'


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
    base64_data = bytes_to_str(latex_to_png(s, encode=True), 'ascii')
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

