# -*- coding: utf-8 -*-
"""Pylab (matplotlib) support utilities.

Authors
-------

* Fernando Perez.
* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from cStringIO import StringIO

from IPython.utils.decorators import flag_calls

# If user specifies a GUI, that dictates the backend, otherwise we read the
# user's mpl default from the mpl rc structure
backends = {'tk': 'TkAgg',
            'gtk': 'GTKAgg',
            'wx': 'WXAgg',
            'qt': 'Qt4Agg', # qt3 not supported
            'qt4': 'Qt4Agg',
            'inline' : 'module://IPython.zmq.pylab.backend_inline'}

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
            figs.append(f.canvas.figure)
        return figs


def figsize(sizex, sizey):
    """Set the default figure size to be [sizex, sizey].

    This is just an easy to remember, convenience wrapper that sets::

      matplotlib.rcParams['figure.figsize'] = [sizex, sizey]
    """
    import matplotlib
    matplotlib.rcParams['figure.figsize'] = [sizex, sizey]


def figure_to_svg(fig):
    """Convert a figure to svg for inline display."""
    fc = fig.get_facecolor()
    ec = fig.get_edgecolor()
    fig.set_facecolor('white')
    fig.set_edgecolor('white')
    try:
        string_io = StringIO()
        fig.canvas.print_figure(string_io, format='svg')
        svg = string_io.getvalue()
    finally:
        fig.set_facecolor(fc)
        fig.set_edgecolor(ec)
    return svg


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


#-----------------------------------------------------------------------------
# Code for initializing matplotlib and importing pylab
#-----------------------------------------------------------------------------


def find_gui_and_backend(gui=None):
    """Given a gui string return the gui and mpl backend.

    Parameters
    ----------
    gui : str
        Can be one of ('tk','gtk','wx','qt','qt4','inline').

    Returns
    -------
    A tuple of (gui, backend) where backend is one of ('TkAgg','GTKAgg',
    'WXAgg','Qt4Agg','module://IPython.zmq.pylab.backend_inline').
    """

    import matplotlib

    if gui:
        # select backend based on requested gui
        backend = backends[gui]
    else:
        backend = matplotlib.rcParams['backend']
        # In this case, we need to find what the appropriate gui selection call
        # should be for IPython, so we can activate inputhook accordingly
        g2b = backends  # maps gui names to mpl backend names
        b2g = dict(zip(g2b.values(), g2b.keys()))  # reverse dict
        gui = b2g.get(backend, None)
    return gui, backend


def activate_matplotlib(backend):
    """Activate the given backend and set interactive to True."""

    import matplotlib
    if backend.startswith('module://'):
        # Work around bug in matplotlib: matplotlib.use converts the
        # backend_id to lowercase even if a module name is specified!
        matplotlib.rcParams['backend'] = backend
    else:
        matplotlib.use(backend)
    matplotlib.interactive(True)

    # This must be imported last in the matplotlib series, after
    # backend/interactivity choices have been made
    import matplotlib.pylab as pylab

    # XXX For now leave this commented out, but depending on discussions with
    # mpl-dev, we may be able to allow interactive switching...
    #import matplotlib.pyplot
    #matplotlib.pyplot.switch_backend(backend)

    pylab.show._needmain = False
    # We need to detect at runtime whether show() is called by the user.
    # For this, we wrap it into a decorator which adds a 'called' flag.
    pylab.draw_if_interactive = flag_calls(pylab.draw_if_interactive)


def import_pylab(user_ns, backend, import_all=True, shell=None):
    """Import the standard pylab symbols into user_ns."""

    # Import numpy as np/pyplot as plt are conventions we're trying to
    # somewhat standardize on.  Making them available to users by default
    # will greatly help this.
    s = ("import numpy\n"
          "import matplotlib\n"
          "from matplotlib import pylab, mlab, pyplot\n"
          "np = numpy\n"
          "plt = pyplot\n"
          )
    exec s in user_ns

    if shell is not None:
        exec s in shell.user_ns_hidden
        # If using our svg payload backend, register the post-execution
        # function that will pick up the results for display.  This can only be
        # done with access to the real shell object.
        if backend == backends['inline']:
            from IPython.zmq.pylab.backend_inline import flush_svg
            from matplotlib import pyplot
            shell.register_post_execute(flush_svg)
            # The typical default figure size is too large for inline use,
            # so we shrink the figure size to 6x4, and tweak fonts to
            # make that fit.  This is configurable via Global.pylab_inline_rc,
            # or rather it will be once the zmq kernel is hooked up to
            # the config system.
            
            default_rc = {
                'figure.figsize': (6.0,4.0),
                # 12pt labels get cutoff on 6x4 logplots, so use 10pt.
                'font.size': 10,
                # 10pt still needs a little more room on the xlabel:
                'figure.subplot.bottom' : .125
            }
            rc = getattr(shell.config.Global, 'pylab_inline_rc', default_rc)
            pyplot.rcParams.update(rc)
            shell.config.Global.pylab_inline_rc = rc
            
            # Add 'figsize' to pyplot and to the user's namespace
            user_ns['figsize'] = pyplot.figsize = figsize
            shell.user_ns_hidden['figsize'] = figsize
        
        # The old pastefig function has been replaced by display
        # Always add this svg formatter so display works.
        from IPython.zmq.pylab.backend_inline import figure_to_svg
        from IPython.core.display import display, display_svg
        svg_formatter = shell.display_formatter.formatters['image/svg+xml']
        svg_formatter.for_type_by_name(
            'matplotlib.figure','Figure',figure_to_svg
        )
        # Add display and display_png to the user's namespace
        user_ns['display'] = display
        shell.user_ns_hidden['display'] = display
        user_ns['display_svg'] = display_svg
        shell.user_ns_hidden['display_svg'] = display_svg
        user_ns['getfigs'] = getfigs
        shell.user_ns_hidden['getfigs'] = getfigs

    if import_all:
        s = ("from matplotlib.pylab import *\n"
             "from numpy import *\n")
        exec s in user_ns
        if shell is not None:
            exec s in shell.user_ns_hidden


def pylab_activate(user_ns, gui=None, import_all=True):
    """Activate pylab mode in the user's namespace.

    Loads and initializes numpy, matplotlib and friends for interactive use.

    Parameters
    ----------
    user_ns : dict
      Namespace where the imports will occur.

    gui : optional, string
      A valid gui name following the conventions of the %gui magic.

    import_all : optional, boolean
      If true, an 'import *' is done from numpy and pylab.

    Returns
    -------
    The actual gui used (if not given as input, it was obtained from matplotlib
    itself, and will be needed next to configure IPython's gui integration.
    """
    gui, backend = find_gui_and_backend(gui)
    activate_matplotlib(backend)
    import_pylab(user_ns, backend)

    print """
Welcome to pylab, a matplotlib-based Python environment [backend: %s].
For more information, type 'help(pylab)'.""" % backend
    
    return gui

