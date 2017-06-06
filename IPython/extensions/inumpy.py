"""Numpy IPython extension
Features:
- Auto complete recarray field names
"""

def install_ipython_completers():
    """Register recarray with IPython tab completion machinery
    """
    from IPython.utils.generics import complete_object
    from numpy import recarray
    @complete_object.when_type(recarray)
    def complete_recarray_colname(obj, prev_completions):
        return prev_completions + list(obj.dtype.names)

def load_ipython_extension(ip):
	install_ipython_completers()
