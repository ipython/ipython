Using dill to expand serialization support
------------------------------------------

adds :func:`~IPython.utils.pickleutil.use_dill` for allowing
dill to extend serialization support in :mod:`IPython.parallel` (closures, etc.).
Also adds :meth:`DirectView.use_dill` convenience method for enabling dill
locally and on all engines with one call.
