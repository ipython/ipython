"""Directives and roles for documenting traitlets config options.

::

    .. configtrait:: Application.log_datefmt

        Description goes here.

    Cross reference like this: :configtrait:`Application.log_datefmt`.
"""


def setup(app):
    app.add_object_type('configtrait', 'configtrait', objname='Config option')
    metadata = {'parallel_read_safe': True, 'parallel_write_safe': True}
    return metadata
