""" Use pretty.py for configurable pretty-printing.

Register pretty-printers for types using pretty.for_type() or
pretty.for_type_by_name(). For example, to make a pretty-printer for numpy dtype
objects, add the following to your ipy_user_conf.py::

    from IPython.Extensions import ipy_pretty, pretty

    def dtype_pprinter(obj, p, cycle):
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

    # If you want to have numpy always imported anyways:
    import numpy
    pretty.for_type(numpy.dtype, dtype_pprinter)

    # If you don't want to have numpy imported until it needs to be:
    pretty.for_type_by_name('numpy', 'dtype', dtype_pprinter)
"""

import IPython.ipapi
from IPython.genutils import Term

from IPython.Extensions import pretty

ip = IPython.ipapi.get()

def pretty_result_display(self, arg):
    """ Uber-pretty-printing display hook.

    Called for displaying the result to the user.
    """
    
    if self.rc.pprint:
        out = pretty.pretty(arg, verbose=getattr(self.rc, 'pretty_verbose', False))
        if '\n' in out:
            # So that multi-line strings line up with the left column of
            # the screen, instead of having the output prompt mess up
            # their first line.                
            Term.cout.write('\n')
        print >>Term.cout, out
    else:
        # By default, the interactive prompt uses repr() to display results,
        # so we should honor this.  Users who'd rather use a different
        # mechanism can easily override this hook.
        print >>Term.cout, repr(arg)
    # the default display hook doesn't manipulate the value to put in history
    return None 

ip.set_hook('result_display', pretty_result_display)

