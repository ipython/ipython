# encoding: utf-8
"""Tests for IPython.utils.path.py"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from unittest.mock import patch
import pytest

from IPython.lib import latextools
from IPython.testing.decorators import onlyif_cmds_exist, skipif_not_matplotlib
from IPython.utils.process import FindCmdError


@pytest.mark.parametrize("command", ('latex', 'dvipng'))
def test_latex_to_png_dvipng_fails_when_no_cmd(command):
    """
    `latex_to_png_dvipng` should return None when there is no required command
    """
    check_latex_to_png_dvipng_fails_when_no_cmd(command)


def check_latex_to_png_dvipng_fails_when_no_cmd(command):
    def mock_find_cmd(arg):
        if arg == command:
            raise FindCmdError

    with patch.object(latextools, "find_cmd", mock_find_cmd):
        assert latextools.latex_to_png_dvipng("whatever", True) is None


@onlyif_cmds_exist('latex', 'dvipng')
@pytest.mark.parametrize("s, wrap", ((u"$$x^2$$", False), (u"x^2", True)))
def test_latex_to_png_dvipng_runs(s, wrap):
    """
    Test that latex_to_png_dvipng just runs without error.
    """
    def mock_kpsewhich(filename):
        assert filename == "breqn.sty"
        return None

    latextools.latex_to_png_dvipng(s, wrap)

    with patch.object(latextools, "kpsewhich", mock_kpsewhich):
        latextools.latex_to_png_dvipng(s, wrap)


@skipif_not_matplotlib
@pytest.mark.parametrize("s, wrap", (("$x^2$", False), ("x^2", True)))
def test_latex_to_png_mpl_runs(s, wrap):
    """
    Test that latex_to_png_mpl just runs without error.
    """
    def mock_kpsewhich(filename):
        assert filename == "breqn.sty"
        return None

    latextools.latex_to_png_mpl(s, wrap)

    with patch.object(latextools, "kpsewhich", mock_kpsewhich):
        latextools.latex_to_png_mpl(s, wrap)

@skipif_not_matplotlib
def test_latex_to_html():
    img = latextools.latex_to_html("$x^2$")
    assert "data:image/png;base64,iVBOR" in img


def test_genelatex_no_wrap():
    """
    Test genelatex with wrap=False.
    """
    def mock_kpsewhich(filename):
        assert False, ("kpsewhich should not be called "
                       "(called with {0})".format(filename))

    with patch.object(latextools, "kpsewhich", mock_kpsewhich):
        assert \
            '\n'.join(latextools.genelatex("body text", False)) == \
            r'''\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
body text
\end{document}'''


def test_genelatex_wrap_with_breqn():
    """
    Test genelatex with wrap=True for the case breqn.sty is installed.
    """
    def mock_kpsewhich(filename):
        assert filename == "breqn.sty"
        return "path/to/breqn.sty"

    with patch.object(latextools, "kpsewhich", mock_kpsewhich):
        assert \
            '\n'.join(latextools.genelatex("x^2", True)) == \
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
\end{document}'''


def test_genelatex_wrap_without_breqn():
    """
    Test genelatex with wrap=True for the case breqn.sty is not installed.
    """
    def mock_kpsewhich(filename):
        assert filename == "breqn.sty"
        return None

    with patch.object(latextools, "kpsewhich", mock_kpsewhich):
        assert \
            '\n'.join(latextools.genelatex("x^2", True)) == \
            r'''\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
$$x^2$$
\end{document}'''


@skipif_not_matplotlib
@onlyif_cmds_exist('latex', 'dvipng')
def test_latex_to_png_color():
    """
    Test color settings for latex_to_png.
    """
    latex_string = "$x^2$"
    default_value = latextools.latex_to_png(latex_string, wrap=False)
    default_hexblack = latextools.latex_to_png(latex_string, wrap=False,
                                               color='#000000')
    dvipng_default = latextools.latex_to_png_dvipng(latex_string, False)
    dvipng_black = latextools.latex_to_png_dvipng(latex_string, False, 'Black')
    assert dvipng_default == dvipng_black
    mpl_default = latextools.latex_to_png_mpl(latex_string, False)
    mpl_black = latextools.latex_to_png_mpl(latex_string, False, 'Black')
    assert mpl_default == mpl_black
    assert default_value in [dvipng_black, mpl_black]
    assert default_hexblack in [dvipng_black, mpl_black]

    # Test that dvips name colors can be used without error
    dvipng_maroon = latextools.latex_to_png_dvipng(latex_string, False,
                                                   'Maroon')
    # And that it doesn't return the black one
    assert dvipng_black != dvipng_maroon

    mpl_maroon = latextools.latex_to_png_mpl(latex_string, False, 'Maroon')
    assert mpl_black != mpl_maroon
    mpl_white = latextools.latex_to_png_mpl(latex_string, False, 'White')
    mpl_hexwhite = latextools.latex_to_png_mpl(latex_string, False, '#FFFFFF')
    assert mpl_white == mpl_hexwhite

    mpl_white_scale = latextools.latex_to_png_mpl(latex_string, False,
                                                  'White', 1.2)
    assert mpl_white != mpl_white_scale


def test_latex_to_png_invalid_hex_colors():
    """
    Test that invalid hex colors provided to dvipng gives an exception.
    """
    latex_string = "$x^2$"
    with pytest.raises(ValueError):
        latextools.latex_to_png(latex_string, backend='dvipng', color="#f00bar")
    with pytest.raises(ValueError):
        latextools.latex_to_png(latex_string, backend='dvipng', color="#f00")
