"""Configurable for configuring the IPython inline backend

This module does not import anything from matplotlib.
"""
#-----------------------------------------------------------------------------
#       Copyright (C) 2011 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.config import Config
from IPython.config.configurable import SingletonConfigurable
from IPython.utils.traitlets import (
    Dict, Instance, CaselessStrEnum, Set, Bool, Int, TraitError, Unicode
)
from IPython.utils.warn import warn

#-----------------------------------------------------------------------------
# Configurable for inline backend options
#-----------------------------------------------------------------------------

def pil_available():
    """Test if PIL/Pillow is available"""
    out = False
    try:
        from PIL import Image
        out = True
    except:
        pass
    return out

# inherit from InlineBackendConfig for deprecation purposes
class InlineBackendConfig(SingletonConfigurable):
    pass

class InlineBackend(InlineBackendConfig):
    """An object to store configuration of the inline backend."""

    def _config_changed(self, name, old, new):
        # warn on change of renamed config section
        if new.InlineBackendConfig != getattr(old, 'InlineBackendConfig', Config()):
            warn("InlineBackendConfig has been renamed to InlineBackend")
        super(InlineBackend, self)._config_changed(name, old, new)

    # The typical default figure size is too large for inline use,
    # so we shrink the figure size to 6x4, and tweak fonts to
    # make that fit.
    rc = Dict({'figure.figsize': (6.0,4.0),
        # play nicely with white background in the Qt and notebook frontend
        'figure.facecolor': (1,1,1,0),
        'figure.edgecolor': (1,1,1,0),
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

    figure_formats = Set({'png'}, config=True,
                          help="""A set of figure formats to enable: 'png', 
                          'retina', 'jpeg', 'svg', 'pdf'.""")

    def _update_figure_formatters(self):
        if self.shell is not None:
            from IPython.core.pylabtools import select_figure_formats
            select_figure_formats(self.shell, self.figure_formats, **self.print_figure_kwargs)
    
    def _figure_formats_changed(self, name, old, new):
        if 'jpg' in new or 'jpeg' in new:
            if not pil_available():
                raise TraitError("Requires PIL/Pillow for JPG figures")
        self._update_figure_formatters()

    figure_format = Unicode(config=True, help="""The figure format to enable (deprecated
                                         use `figure_formats` instead)""")

    def _figure_format_changed(self, name, old, new):
        if new:
            self.figure_formats = {new}

    print_figure_kwargs = Dict({'bbox_inches' : 'tight'}, config=True,
        help="""Extra kwargs to be passed to fig.canvas.print_figure.
        
        Logical examples include: bbox_inches, quality (for jpeg figures), etc.
        """
    )
    _print_figure_kwargs_changed = _update_figure_formatters
    
    close_figures = Bool(True, config=True,
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


