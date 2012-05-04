"""Produce SVG versions of active plots for display by the rich Qt frontend.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Standard library imports
import sys

# Third-party imports
import matplotlib
from matplotlib.backends.backend_agg import new_figure_manager
from matplotlib._pylab_helpers import Gcf

# Local imports.
from IPython.config.configurable import SingletonConfigurable
from IPython.core.displaypub import publish_display_data
from IPython.core.pylabtools import print_figure, select_figure_format
from IPython.utils.traitlets import Dict, Instance, CaselessStrEnum, CBool
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Configurable for inline backend options
#-----------------------------------------------------------------------------
# inherit from InlineBackendConfig for deprecation purposes
class InlineBackendConfig(SingletonConfigurable):
    pass

class InlineBackend(InlineBackendConfig):
    """An object to store configuration of the inline backend."""

    def _config_changed(self, name, old, new):
        # warn on change of renamed config section
        if new.InlineBackendConfig != old.InlineBackendConfig:
            warn("InlineBackendConfig has been renamed to InlineBackend")
        super(InlineBackend, self)._config_changed(name, old, new)

    # The typical default figure size is too large for inline use,
    # so we shrink the figure size to 6x4, and tweak fonts to
    # make that fit.
    rc = Dict({'figure.figsize': (6.0,4.0),
        # 12pt labels get cutoff on 6x4 logplots, so use 10pt.
        'font.size': 10,
        # 72 dpi matches SVG/qtconsole
        # this only affects PNG export, as SVG has no dpi setting
        'savefig.dpi': 72,
        # 10pt still needs a little more room on the xlabel:
        'figure.subplot.bottom' : .125
        }, config=True,
        help="""Subset of matplotlib rcParams that should be different for the
        inline backend."""
    )

    figure_format = CaselessStrEnum(['svg', 'png'], default_value='png', config=True,
        help="The image format for figures with the inline backend.")

    def _figure_format_changed(self, name, old, new):
        if self.shell is None:
            return
        else:
            select_figure_format(self.shell, new)
    
    close_figures = CBool(True, config=True,
        help="""Close all figures at the end of each cell.
        
        When True, ensures that each cell starts with no active figures, but it
        also means that one must keep track of references in order to edit or
        redraw figures in subsequent cells. This mode is ideal for the notebook,
        where residual plots from other cells might be surprising.
        
        When False, one must call figure() to create new figures. This means
        that gcf() and getfigs() can reference figures created in other cells,
        and the active figure can continue to be edited with pylab/pyplot
        methods that reference the current active figure. This mode facilitates
        iterative editing of figures, and behaves most consistently with
        other matplotlib backends, but figure barriers between cells must
        be explicit.
        """)

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')


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
            send_figure(figure_manager.canvas.figure)
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

    fig = Gcf.get_active().canvas.figure

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
        fig.show = lambda *a: send_figure(fig)

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
            try:
                get_ipython
            except NameError:
                raise e
            else:
                get_ipython().showtraceback()
                return
    try:
        # exclude any figures that were closed:
        active = set([fm.canvas.figure for fm in Gcf.get_all_fig_managers()])
        for fig in [ fig for fig in show._to_draw if fig in active ]:
            try:
                send_figure(fig)
            except Exception as e:
                # safely show traceback if in IPython, else raise
                try:
                    get_ipython
                except NameError:
                    raise e
                else:
                    get_ipython().showtraceback()
                    break
    finally:
        # clear flags for next round
        show._to_draw = []
        show._draw_called = False


def send_figure(fig):
    """Draw the given figure and send it as a PNG payload.
    """
    fmt = InlineBackend.instance().figure_format
    data = print_figure(fig, fmt)
    # print_figure will return None if there's nothing to draw:
    if data is None:
        return
    mimetypes = { 'png' : 'image/png', 'svg' : 'image/svg+xml' }
    mime = mimetypes[fmt]
    # flush text streams before sending figures, helps a little with output
    # synchronization in the console (though it's a bandaid, not a real sln)
    sys.stdout.flush(); sys.stderr.flush()
    publish_display_data(
        'IPython.zmq.pylab.backend_inline.send_figure',
        {mime : data}
    )

