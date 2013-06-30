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

from IPython.utils.traitlets import (Unicode, List, Bool)
from IPython.config.configurable import Configurable

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------
           
class GlobalConfigurable(Configurable):
    """Global configurable class for shared config

    Usefull for display data priority that might be use by many trasnformers
    """

    display_data_priority = List(['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text'],
            config=True,
              help= """
                    An ordered list of prefered output type, the first
                    encounterd will usually be used when converting discarding
                    the others.
                    """
            )

    def __init__(self, config=None, **kw):
        super(GlobalConfigurable, self).__init__( config=config, **kw)
