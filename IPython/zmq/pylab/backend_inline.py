"""Produce SVG versions of active plots for display by the rich Qt frontend.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
from cStringIO import StringIO

# System library imports.
import matplotlib
from matplotlib.backends.backend_svg import new_figure_manager
from matplotlib._pylab_helpers import Gcf

# Local imports.
from backend_payload import add_plot_payload

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def show(close=True):
    """Show all figures as SVG payloads sent to the IPython clients.

    Parameters
    ----------
    close : bool, optional
      If true, a ``plt.close('all')`` call is automatically issued after
      sending all the SVG figures.
    """
    for figure_manager in Gcf.get_all_fig_managers():
        send_svg_canvas(figure_manager.canvas)
    if close:
        matplotlib.pyplot.close('all')

# This flag will be reset by draw_if_interactive when called
show._draw_called = False


def paste(*figs):
    """Paste figures into the console workspace.

    If no arguments are given, all available figures are pasted.  If the
    argument list contains references to invalid figures, a warning is printed
    but the function continues pasting further figures.

    Parameters
    ----------
    figs : tuple
      A tuple that can contain any mixture of integers and figure objects.
    """
    if not figs:
        show(close=False)
    else:
        fig_managers = Gcf.get_all_fig_managers()
        fig_index = dict( [(fm.canvas.figure, fm.canvas) for fm in fig_managers]
           + [ (fm.canvas.figure.number, fm.canvas) for fm in fig_managers] )

        for fig in figs:
            canvas = fig_index.get(fig)
            if canvas is None:
                print('Warning: figure %s not available.' % fig)
            else:
                send_svg_canvas(canvas)


def send_svg_canvas(canvas):
    """Draw the current canvas and send it as an SVG payload.
    """
    # Make the background transparent.
    # figure_manager.canvas.figure.patch.set_alpha(0.0)

    # Set the background to white instead so it looks good on black.  We store
    # the current values to restore them at the end.
    fc = canvas.figure.get_facecolor()
    ec = canvas.figure.get_edgecolor()
    canvas.figure.set_facecolor('white')
    canvas.figure.set_edgecolor('white')
    try:
        add_plot_payload('svg', svg_from_canvas(canvas))
    finally:
        canvas.figure.set_facecolor(fc)
        canvas.figure.set_edgecolor(ec)


def svg_from_canvas(canvas):
    """ Return a string containing the SVG representation of a FigureCanvasSvg.
    """
    string_io = StringIO()
    canvas.print_svg(string_io)
    return string_io.getvalue()


def draw_if_interactive():
    """
    Is called after every pylab drawing command
    """
    # We simply flag we were called and otherwise do nothing.  At the end of
    # the code execution, a separate call to show_close() will act upon this.
    show._draw_called = True


def flush_svg():
    """Call show, close all open figures, sending all SVG images.

    This is meant to be called automatically and will call show() if, during
    prior code execution, there had been any calls to draw_if_interactive.
    """
    if show._draw_called:
        show(close=True)
        show._draw_called = False
