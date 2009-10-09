"""Use pretty.py for configurable pretty-printing.

To enable this extension in your configuration
file, add the following to :file:`ipython_config.py`::

    c.Global.extensions = ['IPython.extensions.pretty']
    c.PrettyResultDisplay.verbose = True
    c.PrettyResultDisplay.defaults = [
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
from IPython.core.component import Component
from IPython.utils.traitlets import Bool, List
from IPython.utils.genutils import Term
from IPython.utils.autoattr import auto_attr
from IPython.utils.importstring import import_item

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

_loaded = False


class PrettyResultDisplay(Component):

    verbose = Bool(False, config=True)
    # A list of (module_name, type_name, func_name), like
    # [('numpy', 'dtype', 'IPython.extensions.pretty.dtype_pprinter')]
    defaults = List(default_value=[], config=True)

    def __init__(self, parent, name=None, config=None):
        super(PrettyResultDisplay, self).__init__(parent, name=name, config=config)
        self.setup_defaults()

    def setup_defaults(self):
        """Initialize the default pretty printers."""
        for type_module, type_name, func_name in self.defaults:
            func = import_item(func_name)
            self.for_type_by_name(type_module, type_name, func)

    # Access other components like this rather than by regular attribute
    # access.
    @auto_attr
    def shell(self):
        return Component.get_instances(
            root=self.root,
            klass='IPython.core.iplib.InteractiveShell')[0]

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
        print type_module, type_name, func
        return pretty.for_type_by_name(type_name, type_name, func)


#-----------------------------------------------------------------------------
# Initialization code for the extension
#-----------------------------------------------------------------------------


def load_ipython_extension(ip):
    global _loaded
    if not _loaded:
        prd = PrettyResultDisplay(ip, name='pretty_result_display')
        ip.set_hook('result_display', prd, priority=99)
        _loaded = True

def unload_ipython_extension(ip):
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


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------


def test_pretty():
    """
    In [1]: from IPython.extensions import ipy_pretty

    In [2]: ipy_pretty.activate()

    In [3]: class A(object):
       ...:     def __repr__(self):
       ...:         return 'A()'
       ...:     
       ...:     

    In [4]: a = A()

    In [5]: a
    Out[5]: A()

    In [6]: def a_pretty_printer(obj, p, cycle):
       ...:     p.text('<A>')
       ...:     
       ...:     

    In [7]: ipy_pretty.for_type(A, a_pretty_printer)

    In [8]: a
    Out[8]: <A>

    In [9]: class B(object):
       ...:     def __repr__(self):
       ...:         return 'B()'
       ...:     
       ...:     

    In [10]: B.__module__, B.__name__
    Out[10]: ('__main__', 'B')

    In [11]: def b_pretty_printer(obj, p, cycle):
       ....:     p.text('<B>')
       ....:     
       ....:     

    In [12]: ipy_pretty.for_type_by_name('__main__', 'B', b_pretty_printer)

    In [13]: b = B()

    In [14]: b
    Out[14]: <B>
    """
    assert False, "This should only be doctested, not run."

