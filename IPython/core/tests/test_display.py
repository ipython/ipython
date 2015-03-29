# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import os
import warnings

import nose.tools as nt

from IPython.core import display
from IPython.core.getipython import get_ipython
from IPython.utils import path as ipath

import IPython.testing.decorators as dec

def test_image_size():
    """Simple test for display.Image(args, width=x,height=y)"""
    thisurl = 'http://www.google.fr/images/srpr/logo3w.png'
    img = display.Image(url=thisurl, width=200, height=200)
    nt.assert_equal(u'<img src="%s" width="200" height="200"/>' % (thisurl), img._repr_html_())
    img = display.Image(url=thisurl, width=200)
    nt.assert_equal(u'<img src="%s" width="200"/>' % (thisurl), img._repr_html_())
    img = display.Image(url=thisurl)
    nt.assert_equal(u'<img src="%s"/>' % (thisurl), img._repr_html_())
    img = display.Image(url=thisurl, unconfined=True)
    nt.assert_equal(u'<img src="%s" class="unconfined"/>' % (thisurl), img._repr_html_())

def test_retina_png():
    here = os.path.dirname(__file__)
    img = display.Image(os.path.join(here, "2x2.png"), retina=True)
    nt.assert_equal(img.height, 1)
    nt.assert_equal(img.width, 1)
    data, md = img._repr_png_()
    nt.assert_equal(md['width'], 1)
    nt.assert_equal(md['height'], 1)

def test_retina_jpeg():
    here = os.path.dirname(__file__)
    img = display.Image(os.path.join(here, "2x2.jpg"), retina=True)
    nt.assert_equal(img.height, 1)
    nt.assert_equal(img.width, 1)
    data, md = img._repr_jpeg_()
    nt.assert_equal(md['width'], 1)
    nt.assert_equal(md['height'], 1)

def test_image_filename_defaults():
    '''test format constraint, and validity of jpeg and png'''
    tpath = ipath.get_ipython_package_dir()
    nt.assert_raises(ValueError, display.Image, filename=os.path.join(tpath, 'testing/tests/badformat.gif'),
                     embed=True)
    nt.assert_raises(ValueError, display.Image)
    nt.assert_raises(ValueError, display.Image, data='this is not an image', format='badformat', embed=True)
    from IPython.html import DEFAULT_STATIC_FILES_PATH
    # check boths paths to allow packages to test at build and install time
    imgfile = os.path.join(tpath, 'html/static/base/images/logo.png')
    if not os.path.exists(imgfile):
        imgfile = os.path.join(DEFAULT_STATIC_FILES_PATH, 'base/images/logo.png')
    img = display.Image(filename=imgfile)
    nt.assert_equal('png', img.format)
    nt.assert_is_not_none(img._repr_png_())
    img = display.Image(filename=os.path.join(tpath, 'testing/tests/logo.jpg'), embed=False)
    nt.assert_equal('jpeg', img.format)
    nt.assert_is_none(img._repr_jpeg_())

def _get_inline_config():
    from IPython.kernel.zmq.pylab.config import InlineBackend
    return InlineBackend.instance()
    
@dec.skip_without('matplotlib')
def test_set_matplotlib_close():
    cfg = _get_inline_config()
    cfg.close_figures = False
    display.set_matplotlib_close()
    assert cfg.close_figures
    display.set_matplotlib_close(False)
    assert not cfg.close_figures

_fmt_mime_map = {
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'pdf': 'application/pdf',
    'retina': 'image/png',
    'svg': 'image/svg+xml',
}

@dec.skip_without('matplotlib')
def test_set_matplotlib_formats():
    from matplotlib.figure import Figure
    formatters = get_ipython().display_formatter.formatters
    for formats in [
        ('png',),
        ('pdf', 'svg'),
        ('jpeg', 'retina', 'png'),
        (),
    ]:
        active_mimes = {_fmt_mime_map[fmt] for fmt in formats}
        display.set_matplotlib_formats(*formats)
        for mime, f in formatters.items():
            if mime in active_mimes:
                nt.assert_in(Figure, f)
            else:
                nt.assert_not_in(Figure, f)

@dec.skip_without('matplotlib')
def test_set_matplotlib_formats_kwargs():
    from matplotlib.figure import Figure
    ip = get_ipython()
    cfg = _get_inline_config()
    cfg.print_figure_kwargs.update(dict(foo='bar'))
    kwargs = dict(quality=10)
    display.set_matplotlib_formats('png', **kwargs)
    formatter = ip.display_formatter.formatters['image/png']
    f = formatter.lookup_by_type(Figure)
    cell = f.__closure__[0].cell_contents
    expected = kwargs
    expected.update(cfg.print_figure_kwargs)
    nt.assert_equal(cell, expected)

def test_displayobject_repr():
    h = display.HTML('<br />')
    nt.assert_equal(repr(h), '<IPython.core.display.HTML object>')
    h._show_mem_addr = True
    nt.assert_equal(repr(h), object.__repr__(h))
    h._show_mem_addr = False
    nt.assert_equal(repr(h), '<IPython.core.display.HTML object>')

    j = display.Javascript('')
    nt.assert_equal(repr(j), '<IPython.core.display.Javascript object>')
    j._show_mem_addr = True
    nt.assert_equal(repr(j), object.__repr__(j))
    j._show_mem_addr = False
    nt.assert_equal(repr(j), '<IPython.core.display.Javascript object>')

def test_json():
    d = {'a': 5}
    lis = [d]
    j = display.JSON(d)
    nt.assert_equal(j._repr_json_(), d)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        j = display.JSON(json.dumps(d))
        nt.assert_equal(len(w), 1)
        nt.assert_equal(j._repr_json_(), d)
    
    j = display.JSON(lis)
    nt.assert_equal(j._repr_json_(), lis)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        j = display.JSON(json.dumps(lis))
        nt.assert_equal(len(w), 1)
        nt.assert_equal(j._repr_json_(), lis)
    
    
