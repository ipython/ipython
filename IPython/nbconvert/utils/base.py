"""Global configuration class."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils.traitlets import List
from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Unicode

class NbConvertBase(LoggingConfigurable):
    """Global configurable class for shared config

    Useful for display data priority that might be use by many transformers
    """

    display_data_priority = List(['text/html', 'application/pdf', 'text/latex', 'image/svg+xml', 'image/png', 'image/jpeg', 'text/plain'],
            config=True,
              help= """
                    An ordered list of preferred output type, the first
                    encountered will usually be used when converting discarding
                    the others.
                    """
            )

    default_language = Unicode('ipython', config=True,
       help='DEPRECATED default highlight language, please use language_info metadata instead')

    def __init__(self, **kw):
        super(NbConvertBase, self).__init__(**kw)
