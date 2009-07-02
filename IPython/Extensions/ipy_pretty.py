""" Use pretty.py for configurable pretty-printing.

Register pretty-printers for types using ipy_pretty.for_type() or
ipy_pretty.for_type_by_name(). For example, to use the example pretty-printer
for numpy dtype objects, add the following to your ipy_user_conf.py::

    from IPython.Extensions import ipy_pretty

    ipy_pretty.activate()

    # If you want to have numpy always imported anyways:
    import numpy
    ipy_pretty.for_type(numpy.dtype, ipy_pretty.dtype_pprinter)

    # If you don't want to have numpy imported until it needs to be:
    ipy_pretty.for_type_by_name('numpy', 'dtype', ipy_pretty.dtype_pprinter)
"""

from IPython.core import ipapi
from IPython.utils.genutils import Term

from IPython.external import pretty

ip = ipapi.get()


#### Implementation ############################################################

def pretty_result_display(self, arg):
    """ Uber-pretty-printing display hook.

    Called for displaying the result to the user.
    """
    
    if ip.options.pprint:
        verbose = getattr(ip.options, 'pretty_verbose', False)
        out = pretty.pretty(arg, verbose=verbose)
        if '\n' in out:
            # So that multi-line strings line up with the left column of
            # the screen, instead of having the output prompt mess up
            # their first line.                
            Term.cout.write('\n')
        print >>Term.cout, out
    else:
        raise TryNext


#### API #######################################################################

# Expose the for_type and for_type_by_name functions for easier use.
for_type = pretty.for_type
for_type_by_name = pretty.for_type_by_name


# FIXME: write deactivate(). We need a way to remove a hook.
def activate():
    """ Activate this extension.
    """
    ip.set_hook('result_display', pretty_result_display, priority=99)


#### Example pretty-printers ###################################################

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


#### Tests #####################################################################

def test_pretty():
    """
    In [1]: from IPython.Extensions import ipy_pretty

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

