# -*- coding: utf-8 -*-
"""Top-level display functions for displaying object in different formats.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2008-2010 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Main functions
#-----------------------------------------------------------------------------

def display(obj, include=None, exclude=None):
    """Display a Python object in all frontends.

    By default all representations will be computed and sent to the frontends.
    Frontends can decide which representation is used and how.

    Parameters
    ----------
    obj : object
        The Python object to display.
    include : list or tuple, optional
        A list of format type strings (MIME types) to include in the
        format data dict. If this is set *only* the format types included
        in this list will be computed.
    exclude : list or tuple, optional
        A list of format type string (MIME types) to exclue in the format
        data dict. If this is set all format types will be computed,
        except for those included in this argument.
    """
    from IPython.core.interactiveshell import InteractiveShell
    inst = InteractiveShell.instance()
    format = inst.display_formatter.format
    publish = inst.display_pub.publish

    format_dict = format(obj, include=include, exclude=exclude)
    publish('IPython.core.display.display', format_dict)


def display_pretty(obj):
    """Display the pretty (default) representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
    """
    display(obj, include=['text/plain'])


def display_html(obj):
    """Display the HTML representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
        """
    display(obj, include=['text/plain','text/html'])


def display_svg(obj):
    """Display the SVG representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
    """
    display(obj, include=['text/plain','image/svg+xml'])


def display_png(obj):
    """Display the PNG representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
    """
    display(obj, include=['text/plain','image/png'])


def display_latex(obj):
    """Display the LaTeX representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
    """
    display(obj, include=['text/plain','text/latex'])


def display_json(obj):
    """Display the JSON representation of an object.

    Parameters
    ----------
    obj : object
        The Python object to display.
    """
    display(obj, include=['text/plain','application/json'])



