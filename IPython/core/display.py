# -*- coding: utf-8 -*-
"""Top-level display functions for displaying object in different formats.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import print_function

import os

from .displaypub import (
    publish_pretty, publish_html,
    publish_latex, publish_svg,
    publish_png, publish_json,
    publish_javascript, publish_jpeg
)

from IPython.utils.py3compat import string_types

#-----------------------------------------------------------------------------
# utility functions
#-----------------------------------------------------------------------------

def _safe_exists(path):
    """check path, but don't let exceptions raise"""
    try:
        return os.path.exists(path)
    except Exception:
        return False

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
        The Python objects to display, or if raw=True raw HTML data to
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


def display_jpeg(*objs, **kwargs):
    """Display the JPEG representation of an object.

    Parameters
    ----------
    objs : tuple of objects
        The Python objects to display, or if raw=True raw JPEG data to
        display.
    raw : bool
        Are the data objects raw data or Python objects that need to be
        formatted before display? [default: False]
    """
    raw = kwargs.pop('raw',False)
    if raw:
        for obj in objs:
            publish_jpeg(obj)
    else:
        display(*objs, include=['text/plain','image/jpeg'])


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
    
    Note that not many frontends support displaying JSON.

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

    _read_flags = 'r'

    def __init__(self, data=None, url=None, filename=None):
        """Create a display object given raw data.

        When this object is returned by an expression or passed to the
        display function, it will result in the data being displayed
        in the frontend. The MIME type of the data should match the
        subclasses used, so the Png subclass should be used for 'image/png'
        data. If the data is a URL, the data will first be downloaded
        and then displayed. If

        Parameters
        ----------
        data : unicode, str or bytes
            The raw data or a URL or file to load the data from
        url : unicode
            A URL to download the data from.
        filename : unicode
            Path to a local file to load the data from.
        """
        if data is not None and isinstance(data, string_types):
            if data.startswith('http') and url is None:
                url = data
                filename = None
                data = None
            elif _safe_exists(data) and filename is None:
                url = None
                filename = data
                data = None
        
        self.data = data
        self.url = url
        self.filename = None if filename is None else unicode(filename)
        
        self.reload()

    def reload(self):
        """Reload the raw data from file or URL."""
        if self.filename is not None:
            with open(self.filename, self._read_flags) as f:
                self.data = f.read()
        elif self.url is not None:
            try:
                import urllib2
                response = urllib2.urlopen(self.url)
                self.data = response.read()
                # extract encoding from header, if there is one:
                encoding = None
                for sub in response.headers['content-type'].split(';'):
                    sub = sub.strip()
                    if sub.startswith('charset'):
                        encoding = sub.split('=')[-1].strip()
                        break
                # decode data, if an encoding was specified
                if encoding:
                    self.data = self.data.decode(encoding, 'replace')
            except:
                self.data = None

class Pretty(DisplayObject):

    def _repr_pretty_(self):
        return self.data


class HTML(DisplayObject):

    def _repr_html_(self):
        return self.data


class Math(DisplayObject):

    def _repr_latex_(self):
        s = self.data.strip('$')
        return "$$%s$$" % s


class Latex(DisplayObject):

    def _repr_latex_(self):
        return self.data


class SVG(DisplayObject):
    
    # wrap data in a property, which extracts the <svg> tag, discarding
    # document headers
    _data = None
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, svg):
        if svg is None:
            self._data = None
            return
        # parse into dom object
        from xml.dom import minidom
        x = minidom.parseString(svg)
        # get svg tag (should be 1)
        found_svg = x.getElementsByTagName('svg')
        if found_svg:
            svg = found_svg[0].toxml()
        else:
            # fallback on the input, trust the user
            # but this is probably an error.
            pass
        self._data = svg
    
    def _repr_svg_(self):
        return self.data


class JSON(DisplayObject):

    def _repr_json_(self):
        return self.data

css_t = """$("head").append($("<link/>").attr({
  rel:  "stylesheet",
  type: "text/css",
  href: "%s"
}));
"""

lib_t1 = """$.getScript("%s", function () {
"""
lib_t2 = """});
"""

class Javascript(DisplayObject):

    def __init__(self, data=None, url=None, filename=None, lib=None, css=None):
        """Create a Javascript display object given raw data.

        When this object is returned by an expression or passed to the
        display function, it will result in the data being displayed
        in the frontend. If the data is a URL, the data will first be
        downloaded and then displayed. 
        
        In the Notebook, the containing element will be available as `element`,
        and jQuery will be available.  The output area starts hidden, so if
        the js appends content to `element` that should be visible, then
        it must call `container.show()` to unhide the area.

        Parameters
        ----------
        data : unicode, str or bytes
            The Javascript source code or a URL to download it from.
        url : unicode
            A URL to download the data from.
        filename : unicode
            Path to a local file to load the data from.
        lib : list or str
            A sequence of Javascript library URLs to load asynchronously before
            running the source code. The full URLs of the libraries should
            be given. A single Javascript library URL can also be given as a
            string.
        css: : list or str
            A sequence of css files to load before running the source code.
            The full URLs of the css files should be give. A single css URL
            can also be given as a string.
        """
        if isinstance(lib, basestring):
            lib = [lib]
        elif lib is None:
            lib = []
        if isinstance(css, basestring):
            css = [css]
        elif css is None:
            css = []
        if not isinstance(lib, (list,tuple)):
            raise TypeError('expected sequence, got: %r' % lib)
        if not isinstance(css, (list,tuple)):
            raise TypeError('expected sequence, got: %r' % css)
        self.lib = lib
        self.css = css
        super(Javascript, self).__init__(data=data, url=url, filename=filename)

    def _repr_javascript_(self):
        r = ''
        for c in self.css:
            r += css_t % c
        for l in self.lib:
            r += lib_t1 % l
        r += self.data
        r += lib_t2*len(self.lib)
        return r

# constants for identifying png/jpeg data
_PNG = b'\x89PNG\r\n\x1a\n'
_JPEG = b'\xff\xd8'

class Image(DisplayObject):

    _read_flags = 'rb'
    _FMT_JPEG = u'jpeg'
    _FMT_PNG = u'png'
    _ACCEPTABLE_EMBEDDINGS = [_FMT_JPEG, _FMT_PNG]

    def __init__(self, data=None, url=None, filename=None, format=u'png', embed=None, width=None, height=None):
        """Create a display an PNG/JPEG image given raw data.

        When this object is returned by an expression or passed to the
        display function, it will result in the image being displayed
        in the frontend.

        Parameters
        ----------
        data : unicode, str or bytes
            The raw data or a URL to download the data from.
        url : unicode
            A URL to download the data from.
        filename : unicode
            Path to a local file to load the data from.
        format : unicode
            The format of the image data (png/jpeg/jpg). If a filename or URL is given
            for format will be inferred from the filename extension.
        embed : bool
            Should the image data be embedded using a data URI (True) or be
            loaded using an <img> tag. Set this to True if you want the image
            to be viewable later with no internet connection in the notebook.

            Default is `True`, unless the keyword argument `url` is set, then
            default value is `False`.

            Note that QtConsole is not able to display images if `embed` is set to `False`
        width : int
            Width to which to constrain the image in html
        height : int
            Height to which to constrain the image in html

        Examples
        --------
        # embed implicitly True, works in qtconsole and notebook
        Image('http://www.google.fr/images/srpr/logo3w.png')

        # embed implicitly False, does not works in qtconsole but works in notebook if
        # internet connection available
        Image(url='http://www.google.fr/images/srpr/logo3w.png')

        """
        if filename is not None:
            ext = self._find_ext(filename)
        elif url is not None:
            ext = self._find_ext(url)
        elif data is None:
            raise ValueError("No image data found. Expecting filename, url, or data.")
        elif isinstance(data, string_types) and (
            data.startswith('http') or _safe_exists(data)
        ):
            ext = self._find_ext(data)
        else:
            ext = None

        if ext is not None:
            format = ext.lower()
            if ext == u'jpg' or ext == u'jpeg':
                format = self._FMT_JPEG
            if ext == u'png':
                format = self._FMT_PNG
        elif isinstance(data, bytes) and format == 'png':
            # infer image type from image data header,
            # only if format might not have been specified.
            if data[:2] == _JPEG:
                format = 'jpeg'

        self.format = unicode(format).lower()
        self.embed = embed if embed is not None else (url is None)

        if self.embed and self.format not in self._ACCEPTABLE_EMBEDDINGS:
            raise ValueError("Cannot embed the '%s' image format" % (self.format))
        self.width = width
        self.height = height
        super(Image, self).__init__(data=data, url=url, filename=filename)

    def reload(self):
        """Reload the raw data from file or URL."""
        if self.embed:
            super(Image,self).reload()

    def _repr_html_(self):
        if not self.embed:
            width = height = ''
            if self.width:
                width = ' width="%d"' % self.width
            if self.height:
                height = ' height="%d"' % self.height
            return u'<img src="%s"%s%s/>' % (self.url, width, height)

    def _repr_png_(self):
        if self.embed and self.format == u'png':
            return self.data

    def _repr_jpeg_(self):
        if self.embed and (self.format == u'jpeg' or self.format == u'jpg'):
            return self.data

    def _find_ext(self, s):
        return unicode(s.split('.')[-1].lower())


def clear_output(stdout=True, stderr=True, other=True):
    """Clear the output of the current cell receiving output.
    
    Optionally, each of stdout/stderr or other non-stream data (e.g. anything
    produced by display()) can be excluded from the clear event.
    
    By default, everything is cleared.
    
    Parameters
    ----------
    stdout : bool [default: True]
        Whether to clear stdout.
    stderr : bool [default: True]
        Whether to clear stderr.
    other : bool [default: True]
        Whether to clear everything else that is not stdout/stderr
        (e.g. figures,images,HTML, any result of display()).
    """
    from IPython.core.interactiveshell import InteractiveShell
    if InteractiveShell.initialized():
        InteractiveShell.instance().display_pub.clear_output(
            stdout=stdout, stderr=stderr, other=other,
        )
    else:
        from IPython.utils import io
        if stdout:
            print('\033[2K\r', file=io.stdout, end='')
            io.stdout.flush()
        if stderr:
            print('\033[2K\r', file=io.stderr, end='')
            io.stderr.flush()
        
