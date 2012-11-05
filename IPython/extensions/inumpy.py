"""Numpy IPython extension
Features:
- Auto complete recarray field names
"""

def install_ipython_completers():
    """Register the recarray type with IPython's tab completion machinery, so
    that it knows about accessing column names as attributes."""
    from IPython.utils.generics import complete_object
    from numpy import recarray
    @complete_object.when_type(recarray)
    def complete_recarray_colname(obj, prev_completions):
        return prev_completions + list(obj.dtype.names)


_loaded = False


def load_ipython_extension(ip):
	global _loaded
	if not _loaded:
		install_ipython_completers()
		_loaded = True
