# encoding: utf-8
"""A class for managing IPython extensions.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from collections import OrderedDict
import os
from shutil import copyfile
import sys

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance
from IPython.utils.py3compat import PY3
if PY3:
    from imp import reload

#-----------------------------------------------------------------------------
# Main class
#-----------------------------------------------------------------------------

class ExtensionManager(Configurable):
    """A class to manage IPython extensions.

    An IPython extension is an importable Python module that has
    a function with the signature::

        def load_ipython_extension(ipython):
            # Do things with ipython

    This function is called after your extension is imported and the
    currently active :class:`InteractiveShell` instance is passed as
    the only argument.  You can do anything you want with IPython at
    that point, including defining new magic and aliases, adding new
    components, etc.

    You can also optionally define an :func:`unload_ipython_extension(ipython)`
    function, which will be called if the user unloads or reloads the extension.
    The extension manager will only call :func:`load_ipython_extension` again
    if the extension is reloaded.

    You can put your extension modules anywhere you want, as long as
    they can be imported by Python's standard import mechanism.  However,
    to make it easy to write extensions, you can also put your extensions
    in ``os.path.join(self.ipython_dir, 'extensions')``.  This directory
    is added to ``sys.path`` automatically.
    """

    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')

    def __init__(self, shell=None, **kwargs):
        super(ExtensionManager, self).__init__(shell=shell, **kwargs)
        self.shell.on_trait_change(
            self._on_ipython_dir_changed, 'ipython_dir'
        )
        self.loaded = OrderedDict()

    def __del__(self):
        self.shell.on_trait_change(
            self._on_ipython_dir_changed, 'ipython_dir', remove=True
        )

    @property
    def ipython_extension_dir(self):
        return os.path.join(self.shell.ipython_dir, u'extensions')

    def _on_ipython_dir_changed(self):
        if not os.path.isdir(self.ipython_extension_dir):
            os.makedirs(self.ipython_extension_dir, mode = 0o777)

    def load_extension(self, module_str):
        """Load an IPython extension by its module name.

        Returns the string "already loaded" if the extension is already loaded,
        "no load function" if the module doesn't have a load_ipython_extension
        function, or None if it succeeded.
        """
        if module_str in self.loaded:
            return "already loaded"

        from IPython.utils.syspathcontext import prepended_to_syspath

        with self.shell.builtin_trap:
            if module_str not in sys.modules:
                with prepended_to_syspath(self.ipython_extension_dir):
                    __import__(module_str)
            mod = sys.modules[module_str]
            if self._call_load_ipython_extension(mod):
                self.loaded[module_str] = mod
            else:
                return "no load function"

    def unload_extension(self, module_str):
        """Unload an IPython extension by its module name.

        This function looks up the extension's name in ``sys.modules`` and
        simply calls ``mod.unload_ipython_extension(self)``.

        Returns the string "no unload function" if the extension doesn't define
        a function to unload itself, "not loaded" if the extension isn't loaded,
        otherwise None.
        """
        if module_str not in self.loaded:
            return "not loaded"

        if module_str in sys.modules:
            mod = sys.modules[module_str]
            if self._call_unload_ipython_extension(mod):
                self.loaded.pop(module_str)
            else:
                return "no unload function"

    def reload_extension(self, module_str):
        """Reload an IPython extension by calling reload.

        If the module has not been loaded before,
        :meth:`InteractiveShell.load_extension` is called. Otherwise
        :func:`reload` is called and then the :func:`load_ipython_extension`
        function of the module, if it exists is called.
        """
        from IPython.utils.syspathcontext import prepended_to_syspath

        if (module_str in self.loaded) and (module_str in sys.modules):
            self.unload_extension(module_str)
            mod = sys.modules[module_str]
            with prepended_to_syspath(self.ipython_extension_dir):
                reload(mod)
            if self._call_load_ipython_extension(mod):
                self.loaded[module_str] = mod
        else:
            self.load_extension(module_str)

    def _call_load_ipython_extension(self, mod):
        if hasattr(mod, 'load_ipython_extension'):
            mod.load_ipython_extension(self.shell)
            return True

    def _call_unload_ipython_extension(self, mod):
        if hasattr(mod, 'unload_ipython_extension'):
            mod.unload_ipython_extension(self.shell)
            return True

    def install_extension(self, url, filename=None):
        """Download and install an IPython extension.

        If filename is given, the file will be so named (inside the extension
        directory). Otherwise, the name from the URL will be used. The file must
        have a .py or .zip extension; otherwise, a ValueError will be raised.

        Returns the full path to the installed file.
        """
        # Ensure the extension directory exists
        if not os.path.isdir(self.ipython_extension_dir):
            os.makedirs(self.ipython_extension_dir, mode = 0o777)

        if os.path.isfile(url):
            src_filename = os.path.basename(url)
            copy = copyfile
        else:
            # Deferred imports
            try:
                from urllib.parse import urlparse  # Py3
                from urllib.request import urlretrieve
            except ImportError:
                from urlparse import urlparse
                from urllib import urlretrieve
            src_filename = urlparse(url).path.split('/')[-1]
            copy = urlretrieve

        if filename is None:
            filename = src_filename
        if os.path.splitext(filename)[1] not in ('.py', '.zip'):
            raise ValueError("The file must have a .py or .zip extension", filename)

        filename = os.path.join(self.ipython_extension_dir, filename)
        copy(url, filename)
        return filename

    @staticmethod
    def list_available_extensions():
        """List IPython extensions which define ``ipython_extension``
        setuptools ``entry_points``

        Like so::

            setup(
                #...
                entry_points='''
                [ipython_extensions]
                myextension = myextension_pkg.module
                ''')

        Or like::

            entry_points['ipython_extensions'] = [
                'myextension = myextension_pkg.module']

        """
        import pkg_resources
        return pkg_resources.iter_entry_points(group='ipython_extensions')

    def print_extensions(self):
        """Print the list of IPython extensions which define
        ``ipython_extension`` ``entry_points``, and their source locations
        """
        import pkgutil
        import glob

        print("Loaded:")
        for modulestr, mod in self.loaded.iteritems():
            path_ = mod.__file__
            print(' %s -- %r' % (modulestr, mod.__file__))
        print("")

        print("Available (Registered):")
        for ext in ExtensionManager.list_available_extensions():
            path_ = pkgutil.find_loader(ext.module_name).filename
            print(' %s -- %r' % (ext.name, path_))
        print("")

        print("Available (IPYTHONDIR):")
        for path_ in glob.glob(
            os.path.join(self.ipython_extension_dir, '*.py*')):
            print(' %r' % path_)

        # .. note: If the extension is not listed here, it may very well be
        #    still %load_ext-able. Any Python module with a
        #    load_ipython_extension function may be an IPython extension.
        #    You might consider adding a ipython_extension entrypoint
        #    in the extension; or searching sys.path with something like
        #    grin --sys-path load_ipython_extension
