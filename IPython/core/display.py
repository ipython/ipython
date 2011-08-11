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

from .displaypub import (
    publish_pretty, publish_html,
    publish_latex, publish_svg,
    publish_png, publish_json,
    publish_javascript
)

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


def display_pretty(*objs, **kwargs):
    """Display the pretty (default) representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw text data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_pretty(obj)
    else:
        display(*objs, include=['text/plain'])


def display_html(*objs, **kwargs):
    """Display the HTML representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw html data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_html(obj)
    else:
        display(*objs, include=['text/plain','text/html'])


def display_svg(*objs, **kwargs):
    """Display the SVG representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw svg data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_svg(obj)
    else:
        display(*objs, include=['text/plain','image/svg+xml'])


def display_png(*objs, **kwargs):
    """Display the PNG representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw png data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_png(obj)
    else:
        display(*objs, include=['text/plain','image/png'])


def display_latex(*objs, **kwargs):
    """Display the LaTeX representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw latex data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_latex(obj)
    else:
        display(*objs, include=['text/plain','text/latex'])


def display_json(*objs, **kwargs):
    """Display the JSON representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw json data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_json(obj)
    else:
        display(*objs, include=['text/plain','application/json'])


def display_javascript(*objs, **kwargs):
    """Display the Javascript representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw javascript data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_javascript(obj)
    else:
        display(*objs, include=['text/plain','application/javascript'])

#-----------------------------------------------------------------------------
# Smart classes
#-----------------------------------------------------------------------------


class DisplayObject(object):
    """An object that wraps data to be displayed."""

    def __init__(self, data):
        """Create a display object given raw data of a MIME type or a URL.

        When this object is returned by an expression or passed to the
        display function, it will result in the data being displayed
        in the frontend. The MIME type of the data should match the
        subclasses used, so the Png subclass should be used for 'image/png'
        data. If the data is a URL, the data will first be downloaded
        and then displayed.

        Parameters
        ----------
        data : unicode, str or bytes
            The raw data or a URL to download the data from.
        """
        if data.startswith('http'):
            import urllib2
            response = urllib2.urlopen(data)
            self.data = response.read()
        else:
            self.data = data


class Pretty(DisplayObject):

    def _repr_pretty_(self):
        return self.data


class Html(DisplayObject):

    def _repr_html_(self):
        return self.data


class Latex(DisplayObject):

    def _repr_latex_(self):
        return self.data


class Png(DisplayObject):

    def _repr_png_(self):
        return self.data


class Svg(DisplayObject):

    def _repr_svg_(self):
        return self.data


class Json(DisplayObject):

    def _repr_json_(self):
        return self.data


class Javscript(DisplayObject):

    def _repr_javascript_(self):
        return self.data


