"""Use pretty.py for configurable pretty-printing.

To enable this extension in your configuration
file, add the following to :file:`ipython_config.py`::

    c.Global.extensions = ['IPython.extensions.pretty']
    def dict_pprinter(obj, p, cycle):
        return p.text("<dict>")
    c.PrettyResultDisplay.verbose = True
    c.PrettyResultDisplay.defaults_for_type = [
        (dict, dict_pprinter)
    ]
    c.PrettyResultDisplay.defaults_for_type_by_name = [
        ('numpy', 'dtype', 'IPython.extensions.pretty.dtype_pprinter')
    ]

This extension can also be loaded by using the ``%load_ext`` magic::

    %load_ext IPython.extensions.pretty

If this extension is enabled, you can always add additional pretty printers
by doing::

    ip = get_ipython()
    prd = ip.get_component('pretty_result_display')
    import numpy
    from IPython.extensions.pretty import dtype_pprinter
    prd.for_type(numpy.dtype, dtype_pprinter)

    # If you don't want to have numpy imported until it needs to be:
    prd.for_type_by_name('numpy', 'dtype', dtype_pprinter)
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.error import TryNext
from IPython.external import pretty
from IPython.core.plugin import Plugin
from IPython.utils.traitlets import Bool, List, Instance
from IPython.utils.io import Term
from IPython.utils.autoattr import auto_attr
from IPython.utils.importstring import import_item

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


_loaded = False


class PrettyResultDisplay(Plugin):
    """A component for pretty printing on steroids."""

    verbose = Bool(False, config=True)
    shell = Instance('IPython.core.iplib.InteractiveShellABC')

    # A list of (type, func_name), like
    # [(dict, 'my_dict_printer')]
    # The final argument can also be a callable
    defaults_for_type = List(default_value=[], config=True)

    # A list of (module_name, type_name, func_name), like
    # [('numpy', 'dtype', 'IPython.extensions.pretty.dtype_pprinter')]
    # The final argument can also be a callable
    defaults_for_type_by_name = List(default_value=[], config=True)

    def __init__(self, shell=None, config=None):
        super(PrettyResultDisplay, self).__init__(shell=shell, config=config)
        self._setup_defaults()

    def _setup_defaults(self):
        """Initialize the default pretty printers."""
        for typ, func_name in self.defaults_for_type:
            func = self._resolve_func_name(func_name)
            self.for_type(typ, func)
        for type_module, type_name, func_name in self.defaults_for_type_by_name:
            func = self._resolve_func_name(func_name)
            self.for_type_by_name(type_module, type_name, func)

    def _resolve_func_name(self, func_name):
        if callable(func_name):
            return func_name
        elif isinstance(func_name, basestring):
            return import_item(func_name)
        else:
            raise TypeError('func_name must be a str or callable, got: %r' % func_name)

    def __call__(self, otherself, arg):
        """Uber-pretty-printing display hook.

        Called for displaying the result to the user.
        """
        
        if self.shell.pprint:
            out = pretty.pretty(arg, verbose=self.verbose)
            if '\n' in out:
                # So that multi-line strings line up with the left column of
                # the screen, instead of having the output prompt mess up
                # their first line.                
                Term.cout.write('\n')
            print >>Term.cout, out
        else:
            raise TryNext

    def for_type(self, typ, func):
        """Add a pretty printer for a type."""
        return pretty.for_type(typ, func)

    def for_type_by_name(self, type_module, type_name, func):
        """Add a pretty printer for a type by its name and module name."""
        return pretty.for_type_by_name(type_module, type_name, func)


#-----------------------------------------------------------------------------
# Initialization code for the extension
#-----------------------------------------------------------------------------


def load_ipython_extension(ip):
    """Load the extension in IPython as a hook."""
    global _loaded
    if not _loaded:
        plugin = PrettyResultDisplay(shell=ip, config=ip.config)
        ip.set_hook('result_display', plugin, priority=99)
        _loaded = True
        ip.plugin_manager.register_plugin('pretty_result_display', plugin)

def unload_ipython_extension(ip):
    """Unload the extension."""
    # The hook system does not have a way to remove a hook so this is a pass
    pass


#-----------------------------------------------------------------------------
# Example pretty printers
#-----------------------------------------------------------------------------


def dtype_pprinter(obj, p, cycle):
    """ A pretty-printer for numpy dtype objects.
    """
    if cycle:
        return p.text('dtype(...)')
    if hasattr(obj, 'fields'):
        if obj.fields is None:
            p.text(repr(obj))
        else:
            p.begin_group(7, 'dtype([')
            for i, field in enumerate(obj.descr):
                if i > 0:
                    p.text(',')
                    p.breakable()
                p.pretty(field)
            p.end_group(7, '])')
