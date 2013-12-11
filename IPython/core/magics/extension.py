"""Implementation of magic functions for the extension machinery.
"""
from __future__ import print_function
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

# Stdlib
import os

# Our own packages
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, line_magic

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------

@magics_class
class ExtensionMagics(Magics):
    """Magics to manage the IPython extensions system."""

    @line_magic
    def install_ext(self, parameter_s=''):
        """Download and install an extension from a URL, e.g.::

            %install_ext https://bitbucket.org/birkenfeld/ipython-physics/raw/d1310a2ab15d/physics.py

        The URL should point to an importable Python module - either a .py file
        or a .zip file.

        Parameters:

          -n filename : Specify a name for the file, rather than taking it from
                        the URL.
        """
        opts, args = self.parse_options(parameter_s, 'n:')
        try:
            filename = self.shell.extension_manager.install_extension(args,
                                                                 opts.get('n'))
        except ValueError as e:
            print(e)
            return

        filename = os.path.basename(filename)
        print("Installed %s. To use it, type:" % filename)
        print("  %%load_ext %s" % os.path.splitext(filename)[0])


    @line_magic
    def load_ext(self, module_str):
        """Load an IPython extension by its module name.

        Use ``%lsext`` to list Loaded, Registered, and IPYTHONDIR extensions.
        """
        if not module_str:
            raise UsageError('Missing module name.')
        res = self.shell.extension_manager.load_extension(module_str)

        if res == 'already loaded':
            print("The %s extension is already loaded. To reload it, use:" % module_str)
            print("  %reload_ext", module_str)
        elif res == 'no load function':
            print("The %s module is not an IPython extension." % module_str)

    @line_magic
    def unload_ext(self, module_str):
        """Unload an IPython extension by its module name.

        Not all extensions can be unloaded, only those which define an
        ``unload_ipython_extension`` function.
        """
        if not module_str:
            raise UsageError('Missing module name.')

        res = self.shell.extension_manager.unload_extension(module_str)

        if res == 'no unload function':
            print("The %s extension doesn't define how to unload it." % module_str)
        elif res == "not loaded":
            print("The %s extension is not loaded." % module_str)

    @line_magic
    def reload_ext(self, module_str):
        """Reload an IPython extension by its module name."""
        if not module_str:
            raise UsageError('Missing module name.')
        self.shell.extension_manager.reload_extension(module_str)

    @line_magic
    def lsext(self, _):
        """List Loaded, Registered, and IPYTHONDIR extensions

        * 'Loaded' extensions are already loaded in the IPython config.
        * 'Registered' extensions define  ``ipython_extension``
          ``entry_points`` in their ``setup.py`` files.
        * IPYTHONDIR extensions are located in IPYTHONDIR,
          and must contain a function named ``load_ipython_extension``.

        Any Python module on ``sys.path`` with a ``load_ipython_extension``
        function may be an IPython extension.

        If the extension is not listed here, it may very well be
        still ``%load_ext``-able. You might consider searching
        ``sys.path`` + IPYTHONDIR/extensions for modules with
        ``load_ipython_extension`` functions.
        """
        return self.shell.extension_manager.print_extensions()
