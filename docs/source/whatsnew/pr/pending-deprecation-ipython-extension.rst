Loading extensions from ``ipython_extension_dir`` print a warning that this location is pending
deprecation. This should only affect users still having extensions installed with ``%install_ext``
which has been deprecated since IPython 4.0, and removed in 5.0. extensions still present in
``ipython_extension_dir`` may shadow more recently installed versions using pip. It is thus
recommended to clean ``ipython_extension_dir`` of any extension now available as a package.
