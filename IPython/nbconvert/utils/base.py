"""Global configuration class."""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.utils.traitlets import List
from IPython.config.configurable import LoggingConfigurable
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
           
class NbConvertBase(LoggingConfigurable):
    """Global configurable class for shared config

    Useful for display data priority that might be use by many transformers
    """

    display_data_priority = List(['html', 'application/pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text'],
            config=True,
              help= """
                    An ordered list of preferred output type, the first
                    encountered will usually be used when converting discarding
                    the others.
                    """
            )

    default_language = Unicode('ipython', config=True, help='default highlight language')

    def __init__(self, **kw):
        super(NbConvertBase, self).__init__(**kw)
