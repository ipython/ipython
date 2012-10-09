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

import os
from shutil import copyfile
import sys
from urllib import urlretrieve
from urlparse import urlparse

from IPython.core.error import UsageError
from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Instance

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
    
    You can also optionaly define an :func:`unload_ipython_extension(ipython)`
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

    def __init__(self, shell=None, config=None):
        super(ExtensionManager, self).__init__(shell=shell, config=config)
        self.shell.on_trait_change(
            self._on_ipython_dir_changed, 'ipython_dir'
        )
        self.loaded = set()

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
        otherwise None.
        """
        if module_str in self.loaded:
            return "already loaded"
        
        from IPython.utils.syspathcontext import prepended_to_syspath

        if module_str not in sys.modules:
            with prepended_to_syspath(self.ipython_extension_dir):
                __import__(module_str)
        mod = sys.modules[module_str]
        if self._call_load_ipython_extension(mod):
            self.loaded.add(module_str)

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
                self.loaded.discard(module_str)
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
                self.loaded.add(module_str)
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
            src_filename = urlparse(url).path.split('/')[-1]
            copy = urlretrieve
            
        if filename is None:
            filename = src_filename
        if os.path.splitext(filename)[1] not in ('.py', '.zip'):
            raise ValueError("The file must have a .py or .zip extension", filename)
        
        filename = os.path.join(self.ipython_extension_dir, filename)
        copy(url, filename)
        return filename
