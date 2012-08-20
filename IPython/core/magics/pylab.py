"""Implementation of magic functions for matplotlib/pylab support.
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Our own packages
from IPython.config.application import Application
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@magics_class
class PylabMagics(Magics):
    """Magics related to matplotlib's pylab support"""

    @skip_doctest
    @line_magic
    def pylab(self, parameter_s=''):
        """Load numpy and matplotlib to work interactively.

        %pylab [GUINAME]

        This function lets you activate pylab (matplotlib, numpy and
        interactive support) at any point during an IPython session.

        It will import at the top level numpy as np, pyplot as plt, matplotlib,
        pylab and mlab, as well as all names from numpy and pylab.

        If you are using the inline matplotlib backend for embedded figures,
        you can adjust its behavior via the %config magic::

            # enable SVG figures, necessary for SVG+XHTML export in the qtconsole
            In [1]: %config InlineBackend.figure_format = 'svg'

            # change the behavior of closing all figures at the end of each
            # execution (cell), or allowing reuse of active figures across
            # cells:
            In [2]: %config InlineBackend.close_figures = False

        Parameters
        ----------
        guiname : optional
          One of the valid arguments to the %gui magic ('qt', 'wx', 'gtk',
          'osx' or 'tk').  If given, the corresponding Matplotlib backend is
          used, otherwise matplotlib's default (which you can override in your
          matplotlib config file) is used.

        Examples
        --------
        In this case, where the MPL default is TkAgg::

            In [2]: %pylab

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: TkAgg
            For more information, type 'help(pylab)'.

        But you can explicitly request a different backend::

            In [3]: %pylab qt

            Welcome to pylab, a matplotlib-based Python environment.
            Backend in use: Qt4Agg
            For more information, type 'help(pylab)'.
        """

        if Application.initialized():
            app = Application.instance()
            try:
                import_all_status = app.pylab_import_all
            except AttributeError:
                import_all_status = True
        else:
            import_all_status = True

        self.shell.enable_pylab(parameter_s, import_all=import_all_status, welcome_message=True)
