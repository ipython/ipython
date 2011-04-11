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

def display(*objs, **kwargs):
    """Display a Python object in all frontends.

    By default all representations will be computed and sent to the frontends.
    Frontends can decide which representation is used and how.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    include : list or tuple, optional
        A list of format type strings (MIME types) to include in the
        format data dict. If this is set *only* the format types included
        in this list will be computed.
    exclude : list or tuple, optional
        A list of format type string (MIME types) to exclue in the format
        data dict. If this is set all format types will be computed,
        except for those included in this argument.
    """
    include = kwargs.get('include')
    exclude = kwargs.get('exclude')
    
    from IPython.core.interactiveshell import InteractiveShell
    inst = InteractiveShell.instance()
    format = inst.display_formatter.format
    publish = inst.display_pub.publish

    for obj in objs:
        format_dict = format(obj, include=include, exclude=exclude)
        publish('IPython.core.display.display', format_dict)


def display_pretty(*objs):
    """Display the pretty (default) representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain'])


def display_html(*objs):
    """Display the HTML representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
        """
    display(*objs, include=['text/plain','text/html'])


def display_svg(*objs):
    """Display the SVG representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain','image/svg+xml'])


def display_png(*objs):
    """Display the PNG representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain','image/png'])


def display_latex(*objs):
    """Display the LaTeX representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain','text/latex'])


def display_json(*objs):
    """Display the JSON representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain','application/json'])


def display_javascript(*objs):
    """Display the Javascript representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display.
    """
    display(*objs, include=['text/plain','application/javascript'])
