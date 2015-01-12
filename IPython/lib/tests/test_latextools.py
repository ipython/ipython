# encoding: utf-8
"""Tests for IPython.utils.path.py"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import nose.tools as nt

from IPython.lib import latextools
from IPython.testing.decorators import onlyif_cmds_exist, skipif_not_matplotlib
from IPython.testing.tools import monkeypatch
from IPython.utils.process import FindCmdError


def test_latex_to_png_dvipng_fails_when_no_cmd():
    """
    `latex_to_png_dvipng` should return None when there is no required command
    """
    for command in ['latex', 'dvipng']:
        yield (check_latex_to_png_dvipng_fails_when_no_cmd, command)


def check_latex_to_png_dvipng_fails_when_no_cmd(command):
    def mock_find_cmd(arg):
        if arg == command:
            raise FindCmdError

    with monkeypatch(latextools, "find_cmd", mock_find_cmd):
        nt.assert_equals(latextools.latex_to_png_dvipng("whatever", True),
                         None)


@onlyif_cmds_exist('latex', 'dvipng')
def test_latex_to_png_dvipng_runs():
    """
    Test that latex_to_png_dvipng just runs without error.
    """
    def mock_kpsewhich(filename):
        nt.assert_equals(filename, "breqn.sty")
        return None

    for (s, wrap) in [(u"$$x^2$$", False), (u"x^2", True)]:
        yield (latextools.latex_to_png_dvipng, s, wrap)

        with monkeypatch(latextools, "kpsewhich", mock_kpsewhich):
            yield (latextools.latex_to_png_dvipng, s, wrap)

@skipif_not_matplotlib
def test_latex_to_png_mpl_runs():
    """
    Test that latex_to_png_mpl just runs without error.
    """
    def mock_kpsewhich(filename):
        nt.assert_equals(filename, "breqn.sty")
        return None

    for (s, wrap) in [("$x^2$", False), ("x^2", True)]:
        yield (latextools.latex_to_png_mpl, s, wrap)

        with monkeypatch(latextools, "kpsewhich", mock_kpsewhich):
            yield (latextools.latex_to_png_mpl, s, wrap)

@skipif_not_matplotlib
def test_latex_to_html():
    img = latextools.latex_to_html("$x^2$")
    nt.assert_in("data:image/png;base64,iVBOR", img) 


def test_genelatex_no_wrap():
    """
    Test genelatex with wrap=False.
    """
    def mock_kpsewhich(filename):
        assert False, ("kpsewhich should not be called "
                       "(called with {0})".format(filename))

    with monkeypatch(latextools, "kpsewhich", mock_kpsewhich):
        nt.assert_equals(
            '\n'.join(latextools.genelatex("body text", False)),
            r'''\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
body text
\end{document}''')


def test_genelatex_wrap_with_breqn():
    """
    Test genelatex with wrap=True for the case breqn.sty is installed.
    """
    def mock_kpsewhich(filename):
        nt.assert_equals(filename, "breqn.sty")
        return "path/to/breqn.sty"

    with monkeypatch(latextools, "kpsewhich", mock_kpsewhich):
        nt.assert_equals(
            '\n'.join(latextools.genelatex("x^2", True)),
            r'''\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\usepackage{breqn}
\pagestyle{empty}
\begin{document}
\begin{dmath*}
x^2
\end{dmath*}
\end{document}''')


def test_genelatex_wrap_without_breqn():
    """
    Test genelatex with wrap=True for the case breqn.sty is not installed.
    """
    def mock_kpsewhich(filename):
        nt.assert_equals(filename, "breqn.sty")
        return None

    with monkeypatch(latextools, "kpsewhich", mock_kpsewhich):
        nt.assert_equals(
            '\n'.join(latextools.genelatex("x^2", True)),
            r'''\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
$$x^2$$
\end{document}''')
