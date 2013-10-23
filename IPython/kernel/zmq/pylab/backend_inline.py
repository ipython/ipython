"""A matplotlib backend for publishing figures via display_data"""
#-----------------------------------------------------------------------------
#       Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Third-party imports
import matplotlib
from matplotlib.backends.backend_agg import new_figure_manager, FigureCanvasAgg # analysis: ignore
from matplotlib._pylab_helpers import Gcf

# Local imports
from IPython.core.getipython import get_ipython
from IPython.core.display import display

from .config import InlineBackend

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def show(close=None):
    """Show all figures as SVG/PNG payloads sent to the IPython clients.

    Parameters
    ----------
    close : bool, optional
      If true, a ``plt.close('all')`` call is automatically issued after
      sending all the figures. If this is set, the figures will entirely
      removed from the internal list of figures.
    """
    if close is None:
        close = InlineBackend.instance().close_figures
    try:
        for figure_manager in Gcf.get_all_fig_managers():
            display(figure_manager.canvas.figure)
    finally:
        show._to_draw = []
        if close:
            matplotlib.pyplot.close('all')


# This flag will be reset by draw_if_interactive when called
show._draw_called = False
# list of figures to draw when flush_figures is called
show._to_draw = []


def draw_if_interactive():
    """
    Is called after every pylab drawing command
    """
    # signal that the current active figure should be sent at the end of
    # execution.  Also sets the _draw_called flag, signaling that there will be
    # something to send.  At the end of the code execution, a separate call to
    # flush_figures() will act upon these values
    manager = Gcf.get_active()
    if manager is None:
        return
    fig = manager.canvas.figure

    # Hack: matplotlib FigureManager objects in interacive backends (at least
    # in some of them) monkeypatch the figure object and add a .show() method
    # to it.  This applies the same monkeypatch in order to support user code
    # that might expect `.show()` to be part of the official API of figure
    # objects.
    # For further reference:
    # https://github.com/ipython/ipython/issues/1612
    # https://github.com/matplotlib/matplotlib/issues/835
    
    if not hasattr(fig, 'show'):
        # Queue up `fig` for display
        fig.show = lambda *a: display(fig)

    # If matplotlib was manually set to non-interactive mode, this function
    # should be a no-op (otherwise we'll generate duplicate plots, since a user
    # who set ioff() manually expects to make separate draw/show calls).
    if not matplotlib.is_interactive():
        return

    # ensure current figure will be drawn, and each subsequent call
    # of draw_if_interactive() moves the active figure to ensure it is
    # drawn last
    try:
        show._to_draw.remove(fig)
    except ValueError:
        # ensure it only appears in the draw list once
        pass
    # Queue up the figure for drawing in next show() call
    show._to_draw.append(fig)
    show._draw_called = True


def flush_figures():
    """Send all figures that changed

    This is meant to be called automatically and will call show() if, during
    prior code execution, there had been any calls to draw_if_interactive.
    
    This function is meant to be used as a post_execute callback in IPython,
    so user-caused errors are handled with showtraceback() instead of being
    allowed to raise.  If this function is not called from within IPython,
    then these exceptions will raise.
    """
    if not show._draw_called:
        return
    
    if InlineBackend.instance().close_figures:
        # ignore the tracking, just draw and close all figures
        try:
            return show(True)
        except Exception as e:
            # safely show traceback if in IPython, else raise
            ip = get_ipython()
            if ip is None:
                raise e
            else:
                ip.showtraceback()
                return
    try:
        # exclude any figures that were closed:
        active = set([fm.canvas.figure for fm in Gcf.get_all_fig_managers()])
        for fig in [ fig for fig in show._to_draw if fig in active ]:
            try:
                display(fig)
            except Exception as e:
                # safely show traceback if in IPython, else raise
                ip = get_ipython()
                if ip is None:
                    raise e
                else:
                    ip.showtraceback()
                    return
    finally:
        # clear flags for next round
        show._to_draw = []
        show._draw_called = False


# Changes to matplotlib in version 1.2 requires a mpl backend to supply a default
# figurecanvas. This is set here to a Agg canvas
# See https://github.com/matplotlib/matplotlib/pull/1125
FigureCanvas = FigureCanvasAgg

