# -*- coding: utf-8 -*-
"""Pylab (matplotlib) support utilities.

Authors
-------

* Fernando Perez.
* Brian Granger
"""
from __future__ import print_function

#-----------------------------------------------------------------------------
#  Copyright (C) 2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
from io import BytesIO

from IPython.core.display import _pngxy
from IPython.utils.decorators import flag_calls
from IPython.utils import py3compat

# If user specifies a GUI, that dictates the backend, otherwise we read the
# user's mpl default from the mpl rc structure
backends = {'tk': 'TkAgg',
            'gtk': 'GTKAgg',
            'gtk3': 'GTK3Agg',
            'wx': 'WXAgg',
            'qt': 'Qt4Agg', # qt3 not supported
            'qt4': 'Qt4Agg',
            'osx': 'MacOSX',
            'inline' : 'module://IPython.kernel.zmq.pylab.backend_inline'}

# We also need a reverse backends2guis mapping that will properly choose which
# GUI support to activate based on the desired matplotlib backend.  For the
# most part it's just a reverse of the above dict, but we also need to add a
# few others that map to the same GUI manually:
backend2gui = dict(zip(backends.values(), backends.keys()))
# Our tests expect backend2gui to just return 'qt'
backend2gui['Qt4Agg'] = 'qt'
# In the reverse mapping, there are a few extra valid matplotlib backends that
# map to the same GUI support
backend2gui['GTK'] = backend2gui['GTKCairo'] = 'gtk'
backend2gui['GTK3Cairo'] = 'gtk3'
backend2gui['WX'] = 'wx'
backend2gui['CocoaAgg'] = 'osx'

#-----------------------------------------------------------------------------
# Matplotlib utilities
#-----------------------------------------------------------------------------


def getfigs(*fig_nums):
    """Get a list of matplotlib figures by figure numbers.

    If no arguments are given, all available figures are returned.  If the
    argument list contains references to invalid figures, a warning is printed
    but the function continues pasting further figures.

    Parameters
    ----------
    figs : tuple
        A tuple of ints giving the figure numbers of the figures to return.
    """
    from matplotlib._pylab_helpers import Gcf
    if not fig_nums:
        fig_managers = Gcf.get_all_fig_managers()
        return [fm.canvas.figure for fm in fig_managers]
    else:
        figs = []
        for num in fig_nums:
            f = Gcf.figs.get(num)
            if f is None:
                print('Warning: figure %s not available.' % num)
            else:
                figs.append(f.canvas.figure)
        return figs


def figsize(sizex, sizey):
    """Set the default figure size to be [sizex, sizey].

    This is just an easy to remember, convenience wrapper that sets::

      matplotlib.rcParams['figure.figsize'] = [sizex, sizey]
    """
    import matplotlib
    matplotlib.rcParams['figure.figsize'] = [sizex, sizey]


def print_figure(fig, fmt='png', bbox_inches='tight', **kwargs):
    """Print a figure to an image, and return the resulting file data
    
    Returned data will be bytes unless ``fmt='svg'``,
    in which case it will be unicode.
    
    Any keyword args are passed to fig.canvas.print_figure,
    such as ``quality`` or ``bbox_inches``.
    """
    from matplotlib import rcParams
    # When there's an empty figure, we shouldn't return anything, otherwise we
    # get big blank areas in the qt console.
    if not fig.axes and not fig.lines:
        return

    dpi = rcParams['savefig.dpi']
    if fmt == 'retina':
        dpi = dpi * 2
        fmt = 'png'
    
    # build keyword args
    kw = dict(
        format=fmt,
        fc=fig.get_facecolor(),
        ec=fig.get_edgecolor(),
        dpi=dpi,
        bbox_inches=bbox_inches,
    )
    # **kwargs get higher priority
    kw.update(kwargs)
    
    bytes_io = BytesIO()
    fig.canvas.print_figure(bytes_io, **kw)
    data = bytes_io.getvalue()
    if fmt == 'svg':
        data = data.decode('utf-8')
    return data
    
def retina_figure(fig, **kwargs):
    """format a figure as a pixel-doubled (retina) PNG"""
    pngdata = print_figure(fig, fmt='retina', **kwargs)
    w, h = _pngxy(pngdata)
    metadata = dict(width=w//2, height=h//2)
    return pngdata, metadata

# We need a little factory function here to create the closure where
# safe_execfile can live.
def mpl_runner(safe_execfile):
    """Factory to return a matplotlib-enabled runner for %run.

    Parameters
    ----------
    safe_execfile : function
      This must be a function with the same interface as the
      :meth:`safe_execfile` method of IPython.

    Returns
    -------
    A function suitable for use as the ``runner`` argument of the %run magic
    function.
    """
    
    def mpl_execfile(fname,*where,**kw):
        """matplotlib-aware wrapper around safe_execfile.

        Its interface is identical to that of the :func:`execfile` builtin.

        This is ultimately a call to execfile(), but wrapped in safeties to
        properly handle interactive rendering."""

        import matplotlib
        import matplotlib.pylab as pylab

        #print '*** Matplotlib runner ***' # dbg
        # turn off rendering until end of script
        is_interactive = matplotlib.rcParams['interactive']
        matplotlib.interactive(False)
        safe_execfile(fname,*where,**kw)
        matplotlib.interactive(is_interactive)
        # make rendering call now, if the user tried to do it
        if pylab.draw_if_interactive.called:
            pylab.draw()
            pylab.draw_if_interactive.called = False

    return mpl_execfile


def select_figure_formats(shell, formats, **kwargs):
    """Select figure formats for the inline backend.

    Parameters
    ==========
    shell : InteractiveShell
        The main IPython instance.
    formats : str or set
        One or a set of figure formats to enable: 'png', 'retina', 'jpeg', 'svg', 'pdf'.
    **kwargs : any
        Extra keyword arguments to be passed to fig.canvas.print_figure.
    """
    from matplotlib.figure import Figure
    from IPython.kernel.zmq.pylab import backend_inline

    svg_formatter = shell.display_formatter.formatters['image/svg+xml']
    png_formatter = shell.display_formatter.formatters['image/png']
    jpg_formatter = shell.display_formatter.formatters['image/jpeg']
    pdf_formatter = shell.display_formatter.formatters['application/pdf']

    if isinstance(formats, py3compat.string_types):
        formats = {formats}
    # cast in case of list / tuple
    formats = set(formats)

    [ f.pop(Figure, None) for f in shell.display_formatter.formatters.values() ]
    
    supported = {'png', 'png2x', 'retina', 'jpg', 'jpeg', 'svg', 'pdf'}
    bad = formats.difference(supported)
    if bad:
        bs = "%s" % ','.join([repr(f) for f in bad])
        gs = "%s" % ','.join([repr(f) for f in supported])
        raise ValueError("supported formats are: %s not %s" % (gs, bs))
    
    if 'png' in formats:
        png_formatter.for_type(Figure, lambda fig: print_figure(fig, 'png', **kwargs))
    if 'retina' in formats or 'png2x' in formats:
        png_formatter.for_type(Figure, lambda fig: retina_figure(fig, **kwargs))
    if 'jpg' in formats or 'jpeg' in formats:
        jpg_formatter.for_type(Figure, lambda fig: print_figure(fig, 'jpg', **kwargs))
    if 'svg' in formats:
        svg_formatter.for_type(Figure, lambda fig: print_figure(fig, 'svg', **kwargs))
    if 'pdf' in formats:
        pdf_formatter.for_type(Figure, lambda fig: print_figure(fig, 'pdf', **kwargs))

#-----------------------------------------------------------------------------
# Code for initializing matplotlib and importing pylab
#-----------------------------------------------------------------------------


def find_gui_and_backend(gui=None, gui_select=None):
    """Given a gui string return the gui and mpl backend.

    Parameters
    ----------
    gui : str
        Can be one of ('tk','gtk','wx','qt','qt4','inline').
    gui_select : str
        Can be one of ('tk','gtk','wx','qt','qt4','inline').
        This is any gui already selected by the shell.

    Returns
    -------
    A tuple of (gui, backend) where backend is one of ('TkAgg','GTKAgg',
    'WXAgg','Qt4Agg','module://IPython.kernel.zmq.pylab.backend_inline').
    """

    import matplotlib

    if gui and gui != 'auto':
        # select backend based on requested gui
        backend = backends[gui]
    else:
        # We need to read the backend from the original data structure, *not*
        # from mpl.rcParams, since a prior invocation of %matplotlib may have
        # overwritten that.
        # WARNING: this assumes matplotlib 1.1 or newer!!
        backend = matplotlib.rcParamsOrig['backend']
        # In this case, we need to find what the appropriate gui selection call
        # should be for IPython, so we can activate inputhook accordingly
        gui = backend2gui.get(backend, None)

        # If we have already had a gui active, we need it and inline are the
        # ones allowed.
        if gui_select and gui != gui_select:
            gui = gui_select
            backend = backends[gui]

    return gui, backend


def activate_matplotlib(backend):
    """Activate the given backend and set interactive to True."""

    import matplotlib
    matplotlib.interactive(True)
    
    # Matplotlib had a bug where even switch_backend could not force
    # the rcParam to update. This needs to be set *before* the module
    # magic of switch_backend().
    matplotlib.rcParams['backend'] = backend

    import matplotlib.pyplot
    matplotlib.pyplot.switch_backend(backend)

    # This must be imported last in the matplotlib series, after
    # backend/interactivity choices have been made
    import matplotlib.pylab as pylab

    pylab.show._needmain = False
    # We need to detect at runtime whether show() is called by the user.
    # For this, we wrap it into a decorator which adds a 'called' flag.
    pylab.draw_if_interactive = flag_calls(pylab.draw_if_interactive)


def import_pylab(user_ns, import_all=True):
    """Populate the namespace with pylab-related values.
    
    Imports matplotlib, pylab, numpy, and everything from pylab and numpy.
    
    Also imports a few names from IPython (figsize, display, getfigs)
    
    """

    # Import numpy as np/pyplot as plt are conventions we're trying to
    # somewhat standardize on.  Making them available to users by default
    # will greatly help this.
    s = ("import numpy\n"
          "import matplotlib\n"
          "from matplotlib import pylab, mlab, pyplot\n"
          "np = numpy\n"
          "plt = pyplot\n"
          )
    exec(s, user_ns)
    
    if import_all:
        s = ("from matplotlib.pylab import *\n"
             "from numpy import *\n")
        exec(s, user_ns)
    
    # IPython symbols to add
    user_ns['figsize'] = figsize
    from IPython.core.display import display
    # Add display and getfigs to the user's namespace
    user_ns['display'] = display
    user_ns['getfigs'] = getfigs


def configure_inline_support(shell, backend):
    """Configure an IPython shell object for matplotlib use.

    Parameters
    ----------
    shell : InteractiveShell instance

    backend : matplotlib backend
    """
    # If using our svg payload backend, register the post-execution
    # function that will pick up the results for display.  This can only be
    # done with access to the real shell object.

    # Note: if we can't load the inline backend, then there's no point
    # continuing (such as in terminal-only shells in environments without
    # zeromq available).
    try:
        from IPython.kernel.zmq.pylab.backend_inline import InlineBackend
    except ImportError:
        return
    from matplotlib import pyplot

    cfg = InlineBackend.instance(parent=shell)
    cfg.shell = shell
    if cfg not in shell.configurables:
        shell.configurables.append(cfg)

    if backend == backends['inline']:
        from IPython.kernel.zmq.pylab.backend_inline import flush_figures
        shell.events.register('post_execute', flush_figures)

        # Save rcParams that will be overwrittern
        shell._saved_rcParams = dict()
        for k in cfg.rc:
            shell._saved_rcParams[k] = pyplot.rcParams[k]
        # load inline_rc
        pyplot.rcParams.update(cfg.rc)
    else:
        from IPython.kernel.zmq.pylab.backend_inline import flush_figures
        try:
            shell.events.unregister('post_execute', flush_figures)
        except ValueError:
            pass
        if hasattr(shell, '_saved_rcParams'):
            pyplot.rcParams.update(shell._saved_rcParams)
            del shell._saved_rcParams

    # Setup the default figure format
    select_figure_formats(shell, cfg.figure_formats, **cfg.print_figure_kwargs)

